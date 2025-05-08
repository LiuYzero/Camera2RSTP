import cv2
import subprocess
import sys
from datetime import datetime

def camera_to_rtsp(cam_index=0, rtsp_url='rtsp://192.168.1.108:8554/msi-camera'):
    # 摄像头初始化
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    # 获取摄像头参数
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30  # 默认值

    # FFmpeg命令（关键：通过管道输入帧）
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # 覆盖输出
        '-f', 'rawvideo',  # 输入格式
        '-vcodec', 'rawvideo',  # 原始视频编码
        '-pix_fmt', 'bgr24',  # OpenCV默认像素格式
        '-s', f'{width}x{height}',  # 分辨率
        '-r', str(fps),  # 帧率
        '-i', '-',  # 从标准输入读取
        '-c:v', 'libx264',  # H.264编码
        '-preset', 'ultrafast',  # 快速编码
        '-tune', 'zerolatency',  # 零延迟
        '-f', 'rtsp',  # 输出格式
        rtsp_url  # RTSP地址
    ]

    ffmpeg_cmd += [
        '-x264-params', 'keyint=30:min-keyint=30',  # 关键帧间隔
        '-g', '30',  # GOP大小
        '-bf', '0'  # 禁用B帧
    ]

    # 启动FFmpeg进程
    ffmpeg_process = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        while True:
            ret, frame = cap.read()

            current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")[:-5]
            text_size = cv2.getTextSize(current_time, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            text_x = width - text_size[0] - 20  # 右侧留20像素边距
            text_y = text_size[1] + 10  # 顶部留10像素边距

            # 添加文字和背景框
            cv2.rectangle(frame, (text_x - 5, text_y - text_size[1] - 5),
                          (text_x + text_size[0] + 5, text_y + 5), (0, 0, 0), -1)
            cv2.putText(frame, current_time, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            if not ret:
                print("摄像头读取失败")
                break

            # 将帧写入FFmpeg管道
            ffmpeg_process.stdin.write(frame.tobytes())

    except KeyboardInterrupt:
        print("用户中断")
    finally:
        cap.release()
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()


if __name__ == '__main__':
    # 示例：使用第一个摄像头
    camera_to_rtsp(cam_index=0)