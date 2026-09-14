import base64
import cv2
import numpy as np
from typing import Dict, Any


def perform_error_level_analysis(
    image_bytes: bytes,
    resave_quality: int = 90,
    scale_multiplier: float = 15.0,
) -> Dict[str, Any]:
    """
    Perform Error Level Analysis (ELA) on an input image.
    
    ELA works by re-compressing the image at a known quality level (e.g., 90%)
    and computing the absolute difference between the original and recompressed image.
    Because unaltered regions reach a stable compression error state, areas that have
    been edited, spliced, or resaved separately exhibit distinct error levels.
    """
    # Decode input image bytes into OpenCV BGR image
    nparr = np.frombuffer(image_bytes, np.uint8)
    original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if original is None:
        raise ValueError("Failed to decode image. Ensure valid image file format.")

    # Re-compress in memory as JPEG with specified quality
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), resave_quality]
    _, encoded_jpg = cv2.imencode(".jpg", original, encode_param)
    recompressed = cv2.imdecode(encoded_jpg, cv2.IMREAD_COLOR)

    # Compute absolute difference
    diff = cv2.absdiff(original, recompressed)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    diff_float = diff.astype(np.float32)

    mean_error = float(np.mean(diff_float))
    max_error = float(np.max(diff_float))
    std_error = float(np.std(diff_float))

    # Detect edge / text content regions using Canny edge detector
    orig_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(orig_gray, 50, 150)

    # Statistical block anomaly detection across 32x32 DCT grid blocks
    h, w = gray_diff.shape
    block_size = 32
    active_block_means = []

    for y in range(0, h - (h % block_size), block_size):
        for x in range(0, w - (w % block_size), block_size):
            e_cell = edges[y : y + block_size, x : x + block_size]
            if np.sum(e_cell > 0) > 15:  # Region contains text or borders
                d_cell = gray_diff[y : y + block_size, x : x + block_size]
                cell_mean = float(np.mean(d_cell[e_cell > 0]))
                active_block_means.append(cell_mean)

    if active_block_means and len(active_block_means) >= 10:
        br = np.array(active_block_means)
        median_block = float(np.median(br))
        q25, q75 = float(np.percentile(br, 25)), float(np.percentile(br, 75))
        iqr = max(1e-4, q75 - q25)
        
        # Outlier count: blocks deviating from expected interquartile range
        outliers = np.sum((br < q25 - 1.5 * iqr) | (br > q75 + 1.5 * iqr))
        outlier_ratio = float(outliers) / len(br)
        
        # Variance of text block compression error
        block_std = float(np.std(br))
    else:
        outlier_ratio = 0.0
        outliers = 0
        block_std = 0.0

    # Composite Tamper Risk Score calculation (0.0% to 100.0%)
    # - Authentic documents with uniform compression have near 0 outliers and low block variance.
    # - Spliced/pasted regions cause distinct outlier clusters in active blocks.
    # Base score derived from outlier ratio (up to 70 points) and block disparity (up to 30 points)
    score_outliers = min(70.0, outlier_ratio * 1500.0)
    score_variance = min(30.0, (block_std / 2.5) * 30.0)
    
    # Natural compression noise floor (6-12% for typical JPEG images)
    noise_floor = min(12.0, (mean_error / 2.0) * 10.0)
    
    raw_tamper_score = noise_floor + score_outliers + (score_variance * 0.5)
    tamper_risk_score = round(float(np.clip(raw_tamper_score, 0.0, 100.0)), 2)

    # Classify Tamper Level
    if tamper_risk_score < 25.0:
        tamper_level = "LOW"
        is_tampered = False
        analysis_summary = (
            f"Uniform compression characteristics detected across all content blocks "
            f"(mean error: {mean_error:.2f}, anomalous blocks: {outliers}). No digital manipulation detected."
        )
    elif tamper_risk_score < 50.0:
        tamper_level = "MODERATE"
        is_tampered = False
        analysis_summary = (
            f"Minor compression inconsistencies observed (risk score: {tamper_risk_score}%). "
            f"Consistent with secondary compression, filtering, or mild artifacts."
        )
    elif tamper_risk_score < 75.0:
        tamper_level = "HIGH"
        is_tampered = True
        analysis_summary = (
            f"Significant localized error disparity detected (risk score: {tamper_risk_score}%). "
            f"Found {outliers} anomalous content blocks with divergent compression rates, indicating digital alteration or splicing."
        )
    else:
        tamper_level = "CRITICAL"
        is_tampered = True
        analysis_summary = (
            f"Severe compression anomaly detected (risk score: {tamper_risk_score}%). "
            f"High-frequency error divergence indicates composite elements or pasted modifications."
        )

    # Generate high-contrast ELA visualization map
    ela_visual = np.clip(diff_float * scale_multiplier, 0, 255).astype(np.uint8)
    
    # Convert to base64 PNG data URL
    _, visual_buffer = cv2.imencode(".png", ela_visual)
    ela_base64 = "data:image/png;base64," + base64.b64encode(visual_buffer).decode("utf-8")

    return {
        "tamper_risk_score": tamper_risk_score,
        "tamper_level": tamper_level,
        "is_tampered": is_tampered,
        "mean_error": round(mean_error, 2),
        "max_error": round(max_error, 2),
        "std_error": round(std_error, 2),
        "anomaly_ratio": round(float(outlier_ratio), 4),
        "anomalous_blocks": int(outliers),
        "analysis_summary": analysis_summary,
        "ela_image_base64": ela_base64,
    }
