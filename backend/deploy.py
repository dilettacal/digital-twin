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
    
    # Create data directories in package
    lambda_data_dir = "lambda-package/data"
    lambda_personal_data_dir = os.path.join(lambda_data_dir, "personal_data")
    os.makedirs(lambda_personal_data_dir, exist_ok=True)
    
    # ALWAYS copy prompts directory (required for runtime)
    prompts_source_dir = os.path.join("data", "prompts")
    if os.path.exists(prompts_source_dir):
        print("📋 Copying prompts directory...")
        shutil.copytree(prompts_source_dir, os.path.join(lambda_data_dir, "prompts"))
        print("✅ Prompts directory copied")
    else:
        print("❌ ERROR: prompts directory not found at data/prompts!")
        raise FileNotFoundError("data/prompts directory is required but not found")
    
    # Download personal data from S3 if bucket is specified
    personal_data_bucket = os.getenv("PERSONAL_DATA_BUCKET")
    if personal_data_bucket:
        print(f"📥 Downloading personal data from S3 bucket: {personal_data_bucket}")
        try:
            import boto3
            s3 = boto3.client('s3')
            
            # Download personal data files from S3
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
                    s3.download_file(personal_data_bucket, file_name, os.path.join(lambda_personal_data_dir, file_name))
                    print(f"✅ Downloaded {file_name} from S3")
                except Exception as e:
                    print(f"⚠️  Warning: Could not download {file_name} from S3: {e}")
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not download from S3: {e}")
            print("   Falling back to local data files...")
            # Fall back to local data files if S3 download fails
            personal_data_source_dir = os.path.join("data", "personal_data")
            if os.path.exists(personal_data_source_dir):
                print("📋 Copying local data files...")
                for item in os.listdir(personal_data_source_dir):
                    src_path = os.path.join(personal_data_source_dir, item)
                    dst_path = os.path.join(lambda_personal_data_dir, item)
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                        print(f"✅ Copied directory {item}/")
                    elif os.path.isfile(src_path):
                        shutil.copy2(src_path, dst_path)
                        print(f"✅ Copied {item}")
    else:
        # No S3 bucket configured, use local data files
        print("📋 No PERSONAL_DATA_BUCKET set, copying local data files...")
        personal_data_source_dir = os.path.join("data", "personal_data")
        if os.path.exists(personal_data_source_dir):
            for item in os.listdir(personal_data_source_dir):
                src_path = os.path.join(personal_data_source_dir, item)
                dst_path = os.path.join(lambda_personal_data_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    print(f"✅ Copied directory {item}/")
                elif os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                    print(f"✅ Copied {item}")

    # Verify critical paths exist
    print("\n🔍 Verifying package structure...")
    critical_paths = [
        "lambda-package/app/core/data_loader.py",
        "lambda-package/app/core/prompt_loader.py",
        "lambda-package/data/prompts/system_prompt.txt",
        "lambda-package/data/prompts/critical_rules.txt",
        "lambda-package/data/prompts/proficiency_levels.json",
    ]
    missing_paths = []
    for path in critical_paths:
        if os.path.exists(path):
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ MISSING: {path}")
            missing_paths.append(path)
    
    if missing_paths:
        raise FileNotFoundError(f"Critical files missing from package: {missing_paths}")
    
    # Create zip
    print("\n📦 Creating zip file...")
    with zipfile.ZipFile("lambda-deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("lambda-package"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "lambda-package")
                zipf.write(file_path, arcname)

    # Show package size
    size_mb = os.path.getsize("lambda-deployment.zip") / (1024 * 1024)
    print(f"\n✅ Created lambda-deployment.zip ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()