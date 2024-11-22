import streamlit as st
import pydicom
import numpy as np
from PIL import Image, ImageEnhance

# Function to convert DICOM to a 2D PIL Image
def dicom_to_image(dicom_file, slice_index=0, projection="slice"):
    ds = pydicom.dcmread(dicom_file)
    array = ds.pixel_array

    # Handle 3D arrays
    if len(array.shape) == 3:
        if projection == "slice":
            # Select a specific slice
            array = array[slice_index]
        elif projection == "mean":
            # Use mean intensity projection
            array = np.mean(array, axis=0)
        elif projection == "max":
            # Use maximum intensity projection
            array = np.max(array, axis=0)
        else:
            raise ValueError("Invalid projection method. Choose from 'slice', 'mean', or 'max'.")
    elif len(array.shape) != 2:
        raise ValueError("DICOM pixel array is not 2D or 3D and cannot be visualized directly.")

    # Normalize array to 0-255
    array = (array - np.min(array)) / (np.max(array) - np.min(array)) * 255
    image = Image.fromarray(array.astype(np.uint8))
    return image, ds

# Function to adjust HSL
def adjust_hsl(image, hue, saturation, lightness):
    image = image.convert("RGBA")
    arr = np.array(image).astype(np.float32) / 255.0  # Normalize to 0-1

    # Adjust HSL values
    arr[..., 0] = (arr[..., 0] + hue) % 1.0  # Adjust Hue
    arr[..., 1] = np.clip(arr[..., 1] * saturation, 0, 1)  # Adjust Saturation
    arr[..., 2] = np.clip(arr[..., 2] * lightness, 0, 1)  # Adjust Lightness
    arr = (arr * 255).astype(np.uint8)  # Rescale to 0-255

    return Image.fromarray(arr)

# Streamlit UI
st.title("DICOM Image Analyzer and Manipulator")

uploaded_file = st.file_uploader("Upload a DICOM (.dcm) file", type=["dcm"])

if uploaded_file:
    try:
        st.subheader("DICOM Details")
        projection_method = st.selectbox("Projection Method", ["slice", "mean", "max"])
        slice_index = st.number_input("Slice Index (only for 'slice' projection)", min_value=0, step=1, value=0)
        image, dicom_data = dicom_to_image(uploaded_file, slice_index=slice_index, projection=projection_method)

        st.write(dicom_data)

        st.subheader("Original Image")
        st.image(image, caption="Original DICOM Image", use_column_width=True)

        st.subheader("Adjust Image")
        hue = st.slider("Hue Adjustment", -0.5, 0.5, 0.0, 0.01)
        saturation = st.slider("Saturation Adjustment", 0.5, 1.5, 1.0, 0.01)
        lightness = st.slider("Lightness Adjustment", 0.5, 1.5, 1.0, 0.01)
        brightness = st.slider("Brightness Adjustment", 0.5, 1.5, 1.0, 0.01)

        # Apply adjustments
        enhanced_image = adjust_hsl(image, hue, saturation, lightness)
        enhancer = ImageEnhance.Brightness(enhanced_image)
        final_image = enhancer.enhance(brightness)

        st.subheader("Adjusted Image")
        st.image(final_image, caption="Adjusted DICOM Image", use_column_width=True)

        st.subheader("Download Adjusted Image")
        final_image.save("adjusted_image.png")
        with open("adjusted_image.png", "rb") as file:
            st.download_button(
                label="Download Adjusted Image",
                data=file,
                file_name="adjusted_image.png",
                mime="image/png",
            )
    except Exception as e:
        st.error(f"An error occurred: {e}")
