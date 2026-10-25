# download_real_dataset.py
import urllib.request
import zipfile
import os
import shutil

REPO_ZIP_URL = "https://github.com/interviewstreet/hackerrank-orchestrate-october26/archive/refs/heads/main.zip"
ZIP_FILE = "repo.zip"
EXTRACT_DIR = "repo_extract"

def download_and_extract():
    print("⬇️ Downloading real dataset from GitHub...")
    try:
        urllib.request.urlretrieve(REPO_ZIP_URL, ZIP_FILE)
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return
        
    print("📦 Extracting dataset...")
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
    except Exception as e:
        print(f"❌ Failed to extract: {e}")
        return
        
    # Find the extracted repo directory
    extracted_items = os.listdir(EXTRACT_DIR)
    extracted_repo_dir = None
    for item in extracted_items:
        if item.startswith("hackerrank-orchestrate"):
            extracted_repo_dir = os.path.join(EXTRACT_DIR, item)
            break
            
    if not extracted_repo_dir:
        print("❌ Could not find the extracted repo folder.")
        return
        
    real_dataset_dir = os.path.join(extracted_repo_dir, "dataset")
    
    if not os.path.exists(real_dataset_dir):
        print("❌ Could not find dataset folder in the downloaded repo.")
        return
        
    print("🔄 Replacing mock dataset with real dataset...")
    target_dataset_dir = "dataset"
    
    # Remove old mock dataset
    if os.path.exists(target_dataset_dir):
        shutil.rmtree(target_dataset_dir)
        
    # Move real dataset to the root
    shutil.move(real_dataset_dir, target_dataset_dir)
    
    # Cleanup
    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)
    if os.path.exists(EXTRACT_DIR):
        shutil.rmtree(EXTRACT_DIR)
    
    print("✅ Real dataset successfully downloaded and installed in ./dataset/")
    print("🚀 You can now run 'python main.py' to process the REAL data!")

if __name__ == "__main__":
    download_and_extract()