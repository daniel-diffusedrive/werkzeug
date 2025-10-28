import matplotlib.pyplot as plt

from PIL import Image
import numpy as np

def vis_horizontal(control_image, generated_image):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    # Display images
    axes[0].imshow(control_image)
    axes[0].set_title("Control Image")
    axes[0].axis('off')

    axes[1].imshow(generated_image)
    axes[1].set_title("Generated Image")
    axes[1].axis('off')

    plt.tight_layout()
    plt.show()


def to_overlay_image(control_image, generated_image) -> Image.Image:
    bottom_image = generated_image.copy()
    top_image = control_image.copy()

    # Convert to RGBA if not already
    if bottom_image.mode != 'RGBA':
        bottom_image = bottom_image.convert('RGBA')
    if top_image.mode != 'RGBA':
        top_image = top_image.convert('RGBA')

    # Create a copy of the top image for transparency manipulation
    top_with_alpha = top_image.copy()

    # Convert to numpy array for easier manipulation
    top_array = np.array(top_with_alpha)

    # Make black pixels transparent (threshold can be adjusted)
    # Black pixels have low RGB values, so we check if all channels are below threshold
    threshold = 30  # Adjust this value (0-255) to control what's considered "black"
    black_mask = (top_array[:, :, 0] < threshold) & (top_array[:, :, 1] < threshold) & (top_array[:, :, 2] < threshold)

    # Set alpha channel to 0 for black pixels
    top_array[black_mask, 3] = 0

    # Convert back to PIL Image
    top_with_alpha = Image.fromarray(top_array, 'RGBA')

    # Resize images to same size if needed
    if bottom_image.size != top_with_alpha.size:
        top_with_alpha = top_with_alpha.resize(bottom_image.size, Image.Resampling.LANCZOS)

    # Paste the top image onto the bottom image
    result = bottom_image.copy()
    result.paste(top_with_alpha, (0, 0), top_with_alpha)

    # Display the result
    return result