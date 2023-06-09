
import cv2
import time
import math
import argparse
import onnxruntime
import numpy as np
from math import cos, sin


facing = ""
counting_yaw = 0
count_sum_yaw = 0

def draw_axis(img, yaw, pitch, roll, tdx=None, tdy=None, size=100):
    # Referenced from HopeNet https://github.com/natanielruiz/deep-head-pose
    if math.isnan(yaw) or math.isnan(pitch) or math.isnan(roll):
        return img
    pitch = pitch * np.pi / 180
    yaw = -(yaw * np.pi / 180)
    roll = roll * np.pi / 180
    if tdx != None and tdy != None:
        tdx = tdx
        tdy = tdy
    else:
        height, width = img.shape[:2]
        tdx = width / 2
        tdy = height / 2
    # X-Axis pointing to right. drawn in red
    x1 = size * (cos(yaw) * cos(roll)) + tdx
    y1 = size * (cos(pitch) * sin(roll) + cos(roll) * sin(pitch) * sin(yaw)) + tdy
    # Y-Axis | drawn in green
    #        v
    x2 = size * (-cos(yaw) * sin(roll)) + tdx
    y2 = size * (cos(pitch) * cos(roll) - sin(pitch) * sin(yaw) * sin(roll)) + tdy
    # Z-Axis (out of the screen) drawn in blue
    x3 = size * (sin(yaw)) + tdx
    y3 = size * (-cos(yaw) * sin(pitch)) + tdy
    cv2.line(img, (int(tdx), int(tdy)), (int(x1),int(y1)),(0,0,255),2)
    cv2.line(img, (int(tdx), int(tdy)), (int(x2),int(y2)),(0,255,0),2)
    cv2.line(img, (int(tdx), int(tdy)), (int(x3),int(y3)),(255,0,0),2)
    return img


def main(args):
    # YOLOv4-Head
    yolov4_head = onnxruntime.InferenceSession(
        path_or_bytes=f'yolov4_headdetection_480x640_post.onnx',
        providers=[
            (
                'TensorrtExecutionProvider', {
                    'trt_engine_cache_enable': True,
                    'trt_engine_cache_path': '.',
                    'trt_fp16_enable': True,
                }
            ),
            'CUDAExecutionProvider',
            'CPUExecutionProvider',
        ]
    )
    yolov4_head_input_name = yolov4_head.get_inputs()[0].name
    yolov4_head_H = yolov4_head.get_inputs()[0].shape[2]
    yolov4_head_W = yolov4_head.get_inputs()[0].shape[3]

    # DMHead
    model_file_path = ''
    dmhead_input_name = None
    mask_or_nomask = args.mask_or_nomask

    if mask_or_nomask == 'mask':
        model_file_path = 'dmhead_mask_Nx3x224x224.onnx'
    elif mask_or_nomask == 'nomask':
        model_file_path = 'dmhead_nomask_Nx3x224x224.onnx'

    dmhead = onnxruntime.InferenceSession(
        path_or_bytes=model_file_path,
        providers=[
            (
                'TensorrtExecutionProvider', {
                    'trt_engine_cache_enable': True,
                    'trt_engine_cache_path': '.',
                    'trt_fp16_enable': True,
                }
            ),
            'CUDAExecutionProvider',
            'CPUExecutionProvider',
        ]
    )
    dmhead_input_name = dmhead.get_inputs()[0].name
    dmhead_H = dmhead.get_inputs()[0].shape[2]
    dmhead_W = dmhead.get_inputs()[0].shape[3]

    cap_width = int(args.height_width.split('x')[1])
    cap_height = int(args.height_width.split('x')[0])
    if args.device.isdecimal():
        cap = cv2.VideoCapture(int(args.device))
    else:
        cap = cv2.VideoCapture(args.device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cap_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_height)
    WINDOWS_NAME = 'Demo'
    cv2.namedWindow(WINDOWS_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOWS_NAME, cap_width, cap_height)

    size = (cap_width, cap_height)
    # Below VideoWriter object will create a frame of above defined The output is stored in 'filename.avi' file.
    result = cv2.VideoWriter('output.avi',
                             cv2.VideoWriter_fourcc(*'MJPG'),
                             10, size)
    
    frame_num=0

    while True:
        start = time.time()

        ret, frame = cap.read()
        if not ret:
            continue
        
        frame_num +=1
        print('Frame #: ', frame_num)

        # ============================================================= YOLOv4
        # Resize
        resized_frame = cv2.resize(frame, (yolov4_head_W, yolov4_head_H))
        # BGR to RGB
        rgb = resized_frame[..., ::-1]
        # HWC -> CHW
        chw = rgb.transpose(2, 0, 1)
        # normalize to [0, 1] interval
        chw = np.asarray(chw / 255., dtype=np.float32)
        # hwc --> nhwc
        nchw = chw[np.newaxis, ...]
        # Inference YOLOv4
        heads = yolov4_head.run(
            None,
            input_feed = {yolov4_head_input_name: nchw}
        )[0]

        canvas = resized_frame.copy()
        # ============================================================= DMHead
        croped_resized_frame = None
        scores = heads[:,4]
        keep_idxs = scores > 0.6
        heads = heads[keep_idxs, :]

        if len(heads) > 0:
            dmhead_inputs = []
            dmhead_position = []
            heads[:, 0] = heads[:, 0] * cap_width
            heads[:, 1] = heads[:, 1] * cap_height
            heads[:, 2] = heads[:, 2] * cap_width
            heads[:, 3] = heads[:, 3] * cap_height

            for head in heads:
                x_min = int(head[0])
                y_min = int(head[1])
                x_max = int(head[2])
                y_max = int(head[3])

                # enlarge the bbox to include more background margin
                y_min = max(0, y_min - abs(y_min - y_max) / 10)
                y_max = min(resized_frame.shape[0], y_max + abs(y_min - y_max) / 10)
                x_min = max(0, x_min - abs(x_min - x_max) / 5)
                x_max = min(resized_frame.shape[1], x_max + abs(x_min - x_max) / 5)
                x_max = min(x_max, resized_frame.shape[1])
                croped_frame = resized_frame[int(y_min):int(y_max), int(x_min):int(x_max)]

                # h,w -> 224,224
                croped_resized_frame = cv2.resize(croped_frame, (dmhead_W, dmhead_H))
                # bgr --> rgb
                rgb = croped_resized_frame[..., ::-1]
                # hwc --> chw
                chw = rgb.transpose(2, 0, 1)
                dmhead_inputs.append(chw)
                dmhead_position.append([x_min,y_min,x_max,y_max])
            # chw --> nchw
            nchw = np.asarray(dmhead_inputs, dtype=np.float32)
            positions = np.asarray(dmhead_position, dtype=np.int32)

            yaw = 0.0
            pitch = 0.0
            roll = 0.0
            # Inference DMHead
            outputs = dmhead.run(
                None,
                input_feed = {dmhead_input_name: nchw}
            )[0]

            for (yaw, roll, pitch), position in zip(outputs, positions):
                yaw, pitch, roll = np.squeeze([yaw, pitch, roll])
                print(f'yaw: {int(yaw)}, pitch: {int(pitch)}, roll: {int(roll)}')
                rect_color= (240,0,0)

                # for direction
                global counting_yaw, count_sum_yaw
                if int(yaw)<-10:
                    facing = "Looking Left"
                    counting_yaw += 1 
                elif int(yaw)>10:
                    facing = "Looking Right"
                    counting_yaw += 1 
                elif int(pitch)<-10:
                    facing = "Looking Down"
                elif int(pitch)>10:
                    facing = "Looking Up"
                elif int(yaw)<-170:
                    facing = "Rear"
                elif int(yaw)>170:
                    facing = "Rear"
                else:
                    facing = "Forward"

                    if counting_yaw >= 2:
                        count_sum_yaw += 1
                        counting_yaw = 0

                print(f'total yaw: {count_sum_yaw}\n')
                
                # Alert in terminal
                if count_sum_yaw >= 3:
                    rect_color = (0,0,240) #Changing bbox color to red if there is alert
                    print("*********Alert!!***********")

                x_min,y_min,x_max,y_max = position

                # BBox draw
                cv2.rectangle(
                    canvas,
                    (int(x_min), int(y_min)),
                    (int(x_max), int(y_max)),
                    color = rect_color,
                    thickness=2
                )

                # Draw
                draw_axis(
                    canvas,
                    yaw,
                    pitch,
                    roll,
                    tdx=(x_min+x_max)/2,
                    tdy=(y_min+y_max)/2,
                    size=abs(x_max-x_min)//2
                )
                cv2.putText(
                    canvas,
                    f'yaw: {np.round(yaw)}',
                    (int(x_min), int(y_min)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (100, 255, 0),
                    1
                )
                cv2.putText(
                    canvas,
                    f'pitch: {np.round(pitch)}',
                    (int(x_min), int(y_min) - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (100, 255, 0),
                    1
                )
                cv2.putText(
                    canvas,
                    f'roll: {np.round(roll)}',
                    (int(x_min), int(y_min)-30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (100, 255, 0),
                    1
                )

            cv2.putText(canvas, facing, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(canvas, facing, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA)

        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break

        cv2.imshow(WINDOWS_NAME, canvas)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--device',
        type=str,
        default='0',
        help='Path of the mp4 file or device number of the USB camera. Default: 0',
    )
    parser.add_argument(
        '--height_width',
        type=str,
        default='480x640',
        help='{H}x{W}. Default: 480x640',
    )
    parser.add_argument(
        '--mask_or_nomask',
        type=str,
        default='mask',
        choices=[
            'mask',
            'nomask',
        ],
        help='Select either a model that provides high accuracy when wearing a mask or a model that provides high accuracy when not wearing a mask.',
    )
    args = parser.parse_args()
    main(args)
