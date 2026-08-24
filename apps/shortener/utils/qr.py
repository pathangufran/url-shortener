import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M

def generate_qr_code(data: str) -> io.BytesIO:
    """
    Generate a QR code image for the supplied data.

    Returns:
        BytesIO containing PNG image data.
    """

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    image_buffer = io.BytesIO()

    image.save(
        image_buffer,
        format="PNG",
    )

    image_buffer.seek(0)

    return image_buffer
