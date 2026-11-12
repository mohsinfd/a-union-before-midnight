"""Package existing art inside the vanilla transparent decision-card layout."""
from PIL import Image,ImageOps


def make(source_image,template):
    out=template.convert('RGB').copy()
    # Vanilla's first fourteen rows are the transparent title area. Keep its
    # frame/key pixels and put the illustration in the lower photo rectangle.
    picture=ImageOps.fit(source_image.convert('RGB'),(216,28),method=Image.Resampling.LANCZOS)
    out.paste(picture,(4,17))
    assert all(out.getpixel((x,y))==(0,255,0) for y in range(14) for x in range(out.width))
    return out
