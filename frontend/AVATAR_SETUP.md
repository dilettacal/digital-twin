# Avatar Setup Guide

## Adding Your Avatar Image

To display your personal avatar in the frontend:

1. **Add your avatar image** to the `public` folder:
   - Place your image file as `public/avatar.png` or `public/avatar.jpg`
   - Supported formats: JPG, PNG, WebP
   - Recommended size: At least 400x400 pixels for best quality
   - The image will be automatically cropped to a circle

2. **Image requirements:**
   - Square images work best (1:1 aspect ratio)
   - The image will be displayed in two places:
     - Large avatar in the page header (128x128px)
     - Small avatar in chat messages (40x40px)

3. **Fallback behavior:**
   - If the avatar image doesn't exist, the app will automatically show a gradient placeholder with "DT" initials
   - For chat messages, it will show "You" as a fallback

## Example

```bash
# Place your image in the public folder (PNG or JPG both work!)
cp ~/Pictures/my-photo.png frontend/public/avatar.png
# or
cp ~/Pictures/my-photo.jpg frontend/public/avatar.jpg
```

The avatar will appear automatically once the file is added to the `public` folder!

