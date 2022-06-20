# DMHead
Dual model head pose estimation. Fusion of SOTA models. 360° 6D HeadPose detection.

## 1. Summary
![icon_design drawio (10)](https://user-images.githubusercontent.com/33194443/174505343-43a2c78c-c86a-4e26-810d-b1cf90965a9d.png)

## 2. Atmosphere


## 3. Model Structure
- INPUTS: `Float32 [N,3,224,224]`
- OUTPUTS: `Float32 [N,3]`, `[Yaw,Roll,Pitch]`

![pinheadpose_1x3x224x224 onnx](https://user-images.githubusercontent.com/33194443/174504855-bf03e294-c9c9-477d-9faf-07b3d0393463.png)

## 4. Citation
```
@misc{https://doi.org/10.48550/arxiv.2005.10353,
    doi = {10.48550/ARXIV.2005.10353},
    url = {https://arxiv.org/abs/2005.10353},
    author = {Zhou, Yijun and Gregson, James},
    title = {WHENet: Real-time Fine-Grained Estimation for Wide Range Head Pose},
    publisher = {arXiv},
    year = {2020},
}
```
```
@misc{hempel20226d,
    title={6D Rotation Representation For Unconstrained Head Pose Estimation},
    author={Thorsten Hempel and Ahmed A. Abdelrahman and Ayoub Al-Hamadi},
    year={2022},
    eprint={2202.12555},
    archivePrefix={arXiv},
    primaryClass={cs.CV}
}
```
