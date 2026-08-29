"""
PNG 图像基线对比工具。

容差策略：像素值归一化到 [0, 1] 后计算 RMS 差异，
默认阈值 ``RMS_TOLERANCE``（2%）。尺寸不一致直接判负。
阈值可用环境变量 ``CEDAR_GRAPH_BASELINE_RMS_TOLERANCE`` 覆盖，
以适配字体/地图数据略有差异的运行环境。
"""
import os
from pathlib import Path

import numpy as np
import matplotlib.image as mpimg

#: 默认 RMS 容差（归一化像素值），兼顾字体渲染与抗锯齿差异
RMS_TOLERANCE = float(os.environ.get("CEDAR_GRAPH_BASELINE_RMS_TOLERANCE", "0.02"))


def load_image(path: Path) -> np.ndarray:
    """读取 PNG 为 float 数组，丢弃 alpha 通道。"""
    img = mpimg.imread(str(path))
    if img.dtype != np.float32 and img.dtype != np.float64:
        img = img.astype(np.float64) / np.iinfo(img.dtype).max
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[..., :3]
    return np.asarray(img, dtype=np.float64)


def rms_difference(actual_path: Path, baseline_path: Path) -> float:
    """
    计算两幅 PNG 的归一化 RMS 差异。

    Raises
    ------
    ValueError
        图像尺寸不一致。
    """
    actual = load_image(actual_path)
    baseline = load_image(baseline_path)
    if actual.shape != baseline.shape:
        raise ValueError(
            f"image shape mismatch: actual {actual.shape} vs baseline {baseline.shape}"
        )
    return float(np.sqrt(np.mean((actual - baseline) ** 2)))


def image_metrics(actual_path: Path, baseline_path: Path) -> dict[str, float | int]:
    """Return reproducible pixel-difference evidence for two PNGs."""
    actual = load_image(actual_path)
    baseline = load_image(baseline_path)
    if actual.shape != baseline.shape:
        raise ValueError(
            f"image shape mismatch: actual {actual.shape} vs baseline {baseline.shape}"
        )
    difference = np.abs(actual - baseline)
    return {
        "rms": float(np.sqrt(np.mean(difference ** 2))),
        "max_channel_difference": float(np.max(difference)),
        "different_pixel_count": int(np.count_nonzero(np.any(difference > 0, axis=2))),
    }


def save_difference_image(actual_path: Path, baseline_path: Path, output_path: Path) -> None:
    """Write an RGB absolute-difference heatmap for a parity-test artifact."""
    actual = load_image(actual_path)
    baseline = load_image(baseline_path)
    if actual.shape != baseline.shape:
        raise ValueError(
            f"image shape mismatch: actual {actual.shape} vs baseline {baseline.shape}"
        )
    mpimg.imsave(str(output_path), np.abs(actual - baseline))


def assert_image_match(
        actual_path: Path,
        baseline_path: Path,
        tolerance: float = RMS_TOLERANCE,
):
    """断言 actual 与基线图像的 RMS 差异不超过 tolerance。"""
    if not baseline_path.exists():
        raise AssertionError(
            f"baseline image not found: {baseline_path}. "
            f"Run pytest with --update-baseline to generate it."
        )
    try:
        rms = rms_difference(actual_path, baseline_path)
    except ValueError as e:
        raise AssertionError(
            f"image differs from baseline: {actual_path} vs {baseline_path}: {e}"
        ) from e
    assert rms <= tolerance, (
        f"image differs from baseline: {actual_path} vs {baseline_path}, "
        f"RMS={rms:.4f} > tolerance={tolerance:.4f}"
    )
