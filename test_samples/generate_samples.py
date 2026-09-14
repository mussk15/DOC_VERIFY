import os
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def get_font(size: int, bold: bool = False):
    """Attempt to load a standard TrueType font on Windows, fallback to default."""
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_base_certificate(
    title: str,
    subtitle: str,
    student_name: str,
    student_id: str,
    course: str,
    performance_label: str,
    performance_val: str,
    year_str: str,
    width: int = 1200,
    height: int = 850,
) -> Image.Image:
    """Create a high-fidelity mock academic certificate image."""
    img = Image.new("RGB", (width, height), color=(254, 252, 246))  # Premium parchment/ivory tint
    draw = ImageDraw.Draw(img)

    # Decorative ornamental border
    gold_color = (180, 142, 60)
    navy_color = (18, 38, 70)
    text_color = (30, 30, 30)

    draw.rectangle([(25, 25), (width - 25, height - 25)], outline=navy_color, width=4)
    draw.rectangle([(35, 35), (width - 35, height - 35)], outline=gold_color, width=2)
    draw.rectangle([(42, 42), (width - 42, height - 42)], outline=navy_color, width=1)

    font_header = get_font(34, bold=True)
    font_sub = get_font(18, bold=False)
    font_certify = get_font(20, bold=False)
    font_name = get_font(42, bold=True)
    font_body = get_font(22, bold=False)
    font_meta = get_font(20, bold=True)
    font_seal = get_font(14, bold=True)

    # Institute Header
    draw.text((width // 2, 90), title, fill=navy_color, font=font_header, anchor="mm")
    draw.text((width // 2, 135), subtitle, fill=gold_color, font=font_sub, anchor="mm")

    # Divider line
    draw.line([(width // 2 - 250, 160), (width // 2 + 250, 160)], fill=gold_color, width=2)

    # Certification statement
    draw.text((width // 2, 220), "THIS IS TO CERTIFY THAT", fill=(100, 100, 100), font=font_certify, anchor="mm")

    # Candidate Name
    draw.text((width // 2, 290), student_name, fill=navy_color, font=font_name, anchor="mm")

    # Degree / Program
    draw.text(
        (width // 2, 360),
        f"has successfully fulfilled all institutional criteria for the Degree of",
        fill=text_color,
        font=font_body,
        anchor="mm",
    )
    draw.text((width // 2, 405), course, fill=navy_color, font=get_font(26, bold=True), anchor="mm")

    # Performance / Marks / GPA
    perf_text = f"{performance_label}: {performance_val}"
    draw.text((width // 2, 475), perf_text, fill=(20, 80, 40), font=font_meta, anchor="mm")

    # Identifiers
    draw.text((width // 2, 530), f"Student ID: {student_id}", fill=text_color, font=font_meta, anchor="mm")
    draw.text((width // 2, 570), f"Conferral Year: {year_str}", fill=(80, 80, 80), font=font_sub, anchor="mm")

    # Seal Circle simulation (Gold emblem)
    seal_x, seal_y = 220, 710
    draw.ellipse([(seal_x - 55, seal_y - 55), (seal_x + 55, seal_y + 55)], outline=gold_color, width=3)
    draw.ellipse([(seal_x - 48, seal_y - 48), (seal_x + 48, seal_y + 48)], outline=navy_color, width=1)
    draw.text((seal_x, seal_y - 8), "OFFICIAL", fill=navy_color, font=font_seal, anchor="mm")
    draw.text((seal_x, seal_y + 12), "SEAL", fill=gold_color, font=font_seal, anchor="mm")

    # Signatures
    sig_x = width - 260
    draw.line([(sig_x - 120, seal_y + 15), (sig_x + 120, seal_y + 15)], fill=(60, 60, 60), width=2)
    draw.text((sig_x, seal_y - 15), "Dr. Marcus Sterling", fill=navy_color, font=get_font(18, bold=True), anchor="mm")
    draw.text((sig_x, seal_y + 35), "Registrar & Academic Dean", fill=(100, 100, 100), font=font_sub, anchor="mm")

    return img


def generate_samples(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating mock document samples...")

    # 1. Authentic Sample: Sarah Jenkins
    sarah_img = create_base_certificate(
        title="APEX NATIONAL INSTITUTE OF TECHNOLOGY",
        subtitle="ACCREDITED ACADEMIC CREDENTIAL VERIFICATION SYSTEM",
        student_name="Sarah Jenkins",
        student_id="STU-98421",
        course="B.Sc. Computer Science",
        performance_label="Cumulative GPA",
        performance_val="3.92 GPA",
        year_str="2024",
    )
    # Save with clean single-pass JPEG compression
    sarah_path = output_dir / "sample_authentic_sarah.jpg"
    sarah_img.save(sarah_path, format="JPEG", quality=95)
    print(f" -> Saved {sarah_path.name}")

    # 2. Authentic Sample: David Chen
    david_img = create_base_certificate(
        title="APEX NATIONAL INSTITUTE OF TECHNOLOGY",
        subtitle="ACCREDITED ACADEMIC CREDENTIAL VERIFICATION SYSTEM",
        student_name="David Chen",
        student_id="STU-77210",
        course="B.Tech Electrical Engineering",
        performance_label="Academic Marks",
        performance_val="91.5%",
        year_str="2023",
    )
    david_path = output_dir / "sample_authentic_david.jpg"
    david_img.save(david_path, format="JPEG", quality=95)
    print(f" -> Saved {david_path.name}")

    # 3. Authentic Sample: Elena Rostova
    elena_img = create_base_certificate(
        title="APEX NATIONAL INSTITUTE OF TECHNOLOGY",
        subtitle="ACCREDITED ACADEMIC CREDENTIAL VERIFICATION SYSTEM",
        student_name="Elena Rostova",
        student_id="STU-65872",
        course="M.Sc. Cyber Security & Forensics",
        performance_label="Cumulative GPA",
        performance_val="3.78 GPA",
        year_str="2025",
    )
    elena_path = output_dir / "sample_authentic_elena.jpg"
    elena_img.save(elena_path, format="JPEG", quality=95)
    print(f" -> Saved {elena_path.name}")

    # 4. Unknown Student (Unregistered in database)
    unknown_img = create_base_certificate(
        title="APEX NATIONAL INSTITUTE OF TECHNOLOGY",
        subtitle="ACCREDITED ACADEMIC CREDENTIAL VERIFICATION SYSTEM",
        student_name="Jonathan Doe",
        student_id="STU-99999",
        course="B.Sc. Applied Mathematics",
        performance_label="Cumulative GPA",
        performance_val="3.45 GPA",
        year_str="2024",
    )
    unknown_path = output_dir / "sample_unknown_student.jpg"
    unknown_img.save(unknown_path, format="JPEG", quality=95)
    print(f" -> Saved {unknown_path.name}")

    # 5. Tampered Sample: Sarah Jenkins Certificate with Spliced / Altered GPA
    # We take Sarah's certificate, save as a compressed baseline, then digitally splice a patch
    # that has undergone separate low-quality compression / pixel replacement, simulating digital forgery.
    base_compressed = sarah_img.copy()
    buffer = io.BytesIO()
    base_compressed.save(buffer, format="JPEG", quality=75)
    buffer.seek(0)
    tampered_canvas = Image.open(buffer).copy()

    # Create a spliced patch with a forged GPA "4.00 GPA" or altered name
    patch_w, patch_h = 320, 50
    patch_img = Image.new("RGB", (patch_w, patch_h), color=(254, 252, 246))
    patch_draw = ImageDraw.Draw(patch_img)
    patch_font = get_font(20, bold=True)
    patch_draw.text((patch_w // 2, patch_h // 2), "Cumulative GPA: 4.00 GPA", fill=(220, 20, 20), font=patch_font, anchor="mm")

    # Add noise and harsh compression artifact to the patch to simulate copy-paste from another document
    patch_buf = io.BytesIO()
    patch_img.save(patch_buf, format="JPEG", quality=30)
    patch_buf.seek(0)
    degraded_patch = Image.open(patch_buf)

    # Paste patch directly onto the certificate over the GPA area
    paste_x = (1200 - patch_w) // 2
    paste_y = 450
    tampered_canvas.paste(degraded_patch, (paste_x, paste_y))

    tampered_path = output_dir / "sample_tampered_sarah.jpg"
    tampered_canvas.save(tampered_path, format="JPEG", quality=95)
    print(f" -> Saved {tampered_path.name}")

    print("All sample documents successfully created in:", output_dir)


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    generate_samples(current_dir)
