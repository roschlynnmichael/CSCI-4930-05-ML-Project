import requests
import os
import json

# Setup paths correctly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')
ANIMATIONS_DIR = os.path.join(STATIC_DIR, 'animations')

# Create animations directory if it doesn't exist
os.makedirs(ANIMATIONS_DIR, exist_ok=True)

# List of animations with updated, working URLs from IconScout
animations = {
    'logo.json': 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json',
    'welcome.json': 'https://assets9.lottiefiles.com/packages/lf20_gssu2dkm.json',
    'login.json': 'https://static.lottiefiles.com/animations/login-B2LmhPxTKQ.json',  # Updated
    'register.json': 'https://assets3.lottiefiles.com/packages/lf20_yr6zz3wv.json',
    'error.json': 'https://assets9.lottiefiles.com/packages/lf20_kcsr6fcp.json',
    'about.json': 'https://assets7.lottiefiles.com/packages/lf20_4kx2q32n.json',
    'vision.json': 'https://static.lottiefiles.com/animations/vision-UxR4yNbT7g.json',  # Updated
    'mission.json': 'https://assets1.lottiefiles.com/packages/lf20_hxart9lz.json',
    'values.json': 'https://assets3.lottiefiles.com/packages/lf20_6e0qqtpa.json'
}

def download_animation(filename, url):
    """Download a single animation with error handling"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://lottiefiles.com/',
            'Origin': 'https://lottiefiles.com'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Verify it's valid JSON
        animation_data = response.json()
        
        # Save the animation
        output_path = os.path.join(ANIMATIONS_DIR, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(animation_data, f, indent=2)
        
        print(f'✓ Successfully downloaded {filename}')
        return True
    
    except requests.RequestException as e:
        print(f'✗ Failed to download {filename}: {str(e)}')
        return False
    except json.JSONDecodeError:
        print(f'✗ Invalid JSON data for {filename}')
        return False
    except Exception as e:
        print(f'✗ Unexpected error downloading {filename}: {str(e)}')
        return False

def main():
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Animations Directory: {ANIMATIONS_DIR}")
    print("\nStarting animation downloads...")
    
    successful_downloads = 0
    failed_downloads = []
    
    for filename, url in animations.items():
        if download_animation(filename, url):
            successful_downloads += 1
        else:
            failed_downloads.append(filename)
    
    # Print summary
    print("\nDownload Summary:")
    print(f"✓ Successfully downloaded: {successful_downloads}/{len(animations)}")
    
    if failed_downloads:
        print("\n✗ Failed downloads:")
        for filename in failed_downloads:
            print(f"  - {filename}")
    else:
        print("\nAll animations downloaded successfully!")

if __name__ == "__main__":
    main()