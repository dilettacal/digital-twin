import os
import shutil
import zipfile
import subprocess


def main():
    print("Creating Lambda deployment package...")

    # Clean up
    if os.path.exists("lambda-package"):
        shutil.rmtree("lambda-package")
    if os.path.exists("lambda-deployment.zip"):
        os.remove("lambda-deployment.zip")

    # Create package directory
    os.makedirs("lambda-package")

    # Install dependencies using Docker with Lambda runtime image
    print("Installing dependencies for Lambda runtime...")

    # Use the official AWS Lambda Python 3.12 image
    # This ensures compatibility with Lambda's runtime environment
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.getcwd()}:/var/task",
            "--platform",
            "linux/amd64",  # Force x86_64 architecture
            "--entrypoint",
            "",  # Override the default entrypoint
            "public.ecr.aws/lambda/python:3.12",
            "/bin/sh",
            "-c",
            "pip install --target /var/task/lambda-package -r /var/task/requirements.txt --platform manylinux2014_x86_64 --only-binary=:all: --upgrade",
        ],
        check=True,
    )

    # Copy application files
    print("Copying application files...")
    for file in ["server.py", "lambda_handler.py"]:
        if os.path.exists(file):
            shutil.copy2(file, "lambda-package/")
    
    # Copy app directory
    if os.path.exists("app"):
        shutil.copytree("app", "lambda-package/app")
    
    # Copy data directory
    if os.path.exists("data"):
        shutil.copytree("data", "lambda-package/data")
    
    # Download personal data from S3 if bucket is specified
    personal_data_bucket = os.getenv("PERSONAL_DATA_BUCKET")
    if personal_data_bucket:
        print(f"Downloading personal data from S3 bucket: {personal_data_bucket}")
        try:
            import boto3
            s3 = boto3.client('s3')
            
            # Create data directory in package
            os.makedirs("lambda-package/data", exist_ok=True)
            
            # Download files from S3
            files_to_download = [
                "summary.txt",
                "linkedin.pdf",
                "facts.json",
                "style.txt",
                "me.txt",
                "skills.yml",
                "education.yml",
                "experience.yml",
                "qna.yml",
                "sources.json",
                "resume.md",
            ]
            for file_name in files_to_download:
                try:
                    s3.download_file(personal_data_bucket, file_name, f"lambda-package/data/{file_name}")
                    print(f"✅ Downloaded {file_name} from S3")
                except Exception as e:
                    print(f"⚠️  Warning: Could not download {file_name} from S3: {e}")
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not download from S3: {e}")
            print("   Using local data files if available...")

    # Create zip
    print("Creating zip file...")
    with zipfile.ZipFile("lambda-deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("lambda-package"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "lambda-package")
                zipf.write(file_path, arcname)

    # Show package size
    size_mb = os.path.getsize("lambda-deployment.zip") / (1024 * 1024)
    print(f"✓ Created lambda-deployment.zip ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()