Suspicious Head movement detection using head pose estimation. For the head pose estimation DMHead [Dual model head pose estimation. Fusion of SOTA models. 360° 6D HeadPose detection. All pre-processing and post-processing are fused together, allowing end-to-end processing in a single inference.] was used.

## 1. Summary of DMHead
![icon_design drawio (14)](https://user-images.githubusercontent.com/33194443/175760025-b359e1d2-ac16-456e-8cf6-2c58514fbc7c.png)
- **`[Front side]`** Wearing a mask mode - 6DRepNet (RepVGG-B1g2)

  - Paper
  
    ![image](https://user-images.githubusercontent.com/33194443/175760351-bd8d2e61-bb49-48f3-8023-c45c12cbd800.png)

  - Fine tune (DMHead training)
    ```
    Yaw: 3.3193, Pitch: 4.9063, Roll: 3.3687, MAE: 3.8648
    ```

- **`[Front side]`** Not wearing a mask mode - SynergyNet (MobileNetV2)

  - Paper

    ![image](https://user-images.githubusercontent.com/33194443/174690800-272e5a06-c932-414f-8397-861d7d6284d0.png)

- **`[Rear side]`** WHENet

  - Paper

    ![image](https://user-images.githubusercontent.com/33194443/175760218-4e61da30-71b6-4d2a-8ca4-ddc4c2ec5df0.png)


## 2. Inference Test

```bash
# for yolov4
python track_v4.py \

# for yolov7
python track_v7.py \

[-h] \
[--device DEVICE] \
[--height_width HEIGHT_WIDTH] \
[--mask_or_nomask {mask,nomask}]

optional arguments:
  -h, --help
    Show this help message and exit.

  --device DEVICE
    Path of the mp4 file or device number of the USB camera.
    Default: 0

  --height_width HEIGHT_WIDTH
    {H}x{W}.
    Default: 480x640

  --mask_or_nomask {mask,nomask}
    Select either a model that provides high accuracy when wearing a mask or
    a model that provides high accuracy when not wearing a mask.
    Default: mask
```

## 3. References
1. https://github.com/choyingw/SynergyNet
2. https://github.com/thohemp/6DRepNet
3. https://github.com/Ascend-Research/HeadPoseEstimation-WHENet
4. https://github.com/PINTO0309/Face_Mask_Augmentation
5. https://github.com/PINTO0309/DMHead