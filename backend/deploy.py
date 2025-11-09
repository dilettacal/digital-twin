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
    lambda_prompts_dir = os.path.join(lambda_data_dir, "prompts")
    os.makedirs(lambda_personal_data_dir, exist_ok=True)
    os.makedirs(lambda_prompts_dir, exist_ok=True)
    prompts_template_dir = os.path.join("data", "prompts_template")
    
    # Download personal data from S3 if bucket is specified
    personal_data_bucket = os.getenv("PERSONAL_DATA_BUCKET")
    prompts_synced = False
    if personal_data_bucket:
        print(f"📥 Downloading personal data from S3 bucket: {personal_data_bucket}")
        try:
            import boto3
            s3 = boto3.client('s3')
            
            # Download personal data files from S3 (under personal_data/ prefix)
            print("📥 Downloading personal data files from S3...")
            paginator = s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=personal_data_bucket, Prefix="personal_data/"):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith("/"):
                        continue
                    relative_path = key[len("personal_data/"):]
                    if not relative_path:
                        continue
                    destination_path = os.path.join(lambda_personal_data_dir, relative_path)
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    try:
                        s3.download_file(personal_data_bucket, key, destination_path)
                        print(f"✅ Downloaded {relative_path} from S3")
                    except Exception as e:
                        print(f"⚠️  Warning: Could not download {key} from S3: {e}")

            # Download prompts directory from S3 (prefix: prompts/)
            print("📥 Downloading prompts from S3...")
            paginator = s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=personal_data_bucket, Prefix="prompts/"):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith("/"):
                        continue
                    relative_path = key[len("prompts/"):]
                    if not relative_path:
                        continue
                    destination_path = os.path.join(lambda_prompts_dir, relative_path)
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    try:
                        s3.download_file(personal_data_bucket, key, destination_path)
                        prompts_synced = True
                        print(f"✅ Downloaded prompt {relative_path} from S3")
                    except Exception as e:
                        print(f"⚠️  Warning: Could not download prompt {key} from S3: {e}")
                    
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
            prompts_source_dir = os.path.join("data", "prompts")
            if os.path.exists(prompts_source_dir) and os.listdir(prompts_source_dir):
                shutil.copytree(prompts_source_dir, lambda_prompts_dir, dirs_exist_ok=True)
                prompts_synced = True
                print("✅ Copied prompts directory from local data")
        if personal_data_bucket and not prompts_synced:
            prompts_source_dir = os.path.join("data", "prompts")
            if os.path.exists(prompts_source_dir) and os.listdir(prompts_source_dir):
                shutil.copytree(prompts_source_dir, lambda_prompts_dir, dirs_exist_ok=True)
                prompts_synced = True
                print("⚠️  Warning: Using local prompts directory because S3 prompts were unavailable")
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
        prompts_source_dir = os.path.join("data", "prompts")
        if os.path.exists(prompts_source_dir) and os.listdir(prompts_source_dir):
            shutil.copytree(prompts_source_dir, lambda_prompts_dir, dirs_exist_ok=True)
            prompts_synced = True
            print("✅ Copied prompts directory from local data")

    required_prompt_files = [
        "system_prompt.txt",
        "critical_rules.txt",
        "proficiency_levels.json",
    ]

    missing_required_prompts = []
    for prompt_file in required_prompt_files:
        target_path = os.path.join(lambda_prompts_dir, prompt_file)
        if not os.path.exists(target_path):
            missing_required_prompts.append(prompt_file)

    if missing_required_prompts and os.path.exists(prompts_template_dir):
        print("📄 Filling missing prompt files from prompts_template...")
        for prompt_file in missing_required_prompts:
            src = os.path.join(prompts_template_dir, prompt_file)
            dst = os.path.join(lambda_prompts_dir, prompt_file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"  ✅ Copied {prompt_file} from prompts_template")
            else:
                print(f"  ⚠️  Template for {prompt_file} not found in prompts_template")

    for prompt_file in required_prompt_files:
        if not os.path.exists(os.path.join(lambda_prompts_dir, prompt_file)):
            raise FileNotFoundError(
                f"Prompt file '{prompt_file}' is required but was not found. "
                "Ensure prompts are available in S3, data/prompts, or data/prompts_template."
            )

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