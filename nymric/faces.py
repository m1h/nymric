import asyncio
import io


def available():
    try:
        import PIL.Image  # noqa: F401
        return True
    except ImportError:
        return False


def dhash(data):
    from PIL import Image
    img = Image.open(io.BytesIO(data)).convert("L").resize((9, 8))
    px = img.tobytes()
    bits = 0
    for row in range(8):
        for col in range(8):
            i = row * 9 + col
            bits = (bits << 1) | int(px[i] > px[i + 1])
    return bits


def hamming(a, b):
    return bin(a ^ b).count("1")


async def fingerprint(client, hits):
    async def one(h):
        if h.state != "found" or not h.avatar:
            return
        try:
            r = await client.get(h.avatar)
            if r.status_code == 200 and r.content:
                h.ahash = dhash(r.content)
        except Exception:
            pass

    await asyncio.gather(*(one(h) for h in hits))
