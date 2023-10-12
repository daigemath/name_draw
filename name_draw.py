from PIL import Image, ImageDraw, ImageTk,ImageFilter# 图片处理
import tkinter as tk  #构建窗口用
from tkinter import filedialog

# 加密使用
import wmi
import os
import time
import json

import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

皮肤像素点 =  (161, 109, 88)
叠加行 = 4
叠加列 = 6

#加密使用代码
class My_AES_CBC():
    def __init__(self, key, iv):
        # key 和 iv 必须为 16 位
        self.key = key
        self.mode = AES.MODE_CBC
        self.cryptor = AES.new(self.key, self.mode, iv)

    def encrypt(self, plain_text):
        encode_text = plain_text.encode('utf-8')
        pad_text = pad(encode_text, AES.block_size)
        encrypted_text = self.cryptor.encrypt(pad_text)
        # base64_text = base64.b32encode(encrypted_text)
        return encrypted_text

    def decrypt(self, encrypted_text):
        plain_text = self.cryptor.decrypt(encrypted_text)
        plain_text = unpad(plain_text, AES.block_size).decode()
        return plain_text

class Register:
    def __init__(self):
        self.Aes_key = '9B8FD68A366F4D03'.encode()
        self.Aes_IV = '305FB72D83134CA0'.encode('utf-8')
        
        self.pre_str = "HJDKAH"   # 前缀
        self.suf_str = "SDFDTY"   # 后缀
        
        # 获取机器码，机器码由以下四部分拼接组成
        # 1、CPU序列号  2、MAC地址 3.硬盘序列号 4.主板序列号
        self.m_wmi = wmi.WMI()
 
    #cpu序列号 16位
    def get_cpu_serial(self):
        cpu_info = self.m_wmi.Win32_Processor()
        if len(cpu_info) > 0:
            serial_number = cpu_info[0].ProcessorId
            return serial_number
        else:
            return "ABCDEFGHIJKLMNOP"
 
    #硬盘序列号 15位
    def get_disk_serial(self):
        disk_info = self.m_wmi.Win32_PhysicalMedia()
        disk_info.sort()
        if len(disk_info) > 0:
            serial_number = disk_info[0].SerialNumber.strip()
            return serial_number
        else:
            return "WD-ABCDEFGHIJKL"
 
    #mac地址 12位
    def get_mac_address(self):
        for network in self.m_wmi.Win32_NetworkAdapterConfiguration():
            mac_address = network.MacAddress
            if mac_address != None:
                return mac_address.replace(":", "")
        return "ABCDEF123456"
 
    #主板序列号 14位
    def get_board_serial(self):
        board_info = self.m_wmi.Win32_BaseBoard()
        if len(board_info) > 0:
            board_id = board_info[0].SerialNumber.strip().strip('.')
            return board_id
        else:
            return "ABCDEFGHIJKLMN"
 
    # 拼接生成机器码
    def getMachineCode(self):
        mac_address = self.get_mac_address()
        cpu_serial = self.get_cpu_serial()
        disk_serial = self.get_disk_serial()
        board_serial = self.get_board_serial()
        
        combine_str = self.pre_str + mac_address + cpu_serial + disk_serial + board_serial + self.suf_str
        combine_byte = combine_str.encode("utf-8")
        machine_code = hashlib.md5(combine_byte).hexdigest()
        return machine_code.upper()
 
    # AES_CBC 加密
    def Encrypt(self, plain_text):
        e = My_AES_CBC(self.Aes_key, self.Aes_IV).encrypt(plain_text)
        return e
        
    # AES_CBC 解密
    def Decrypt(self, encrypted_text):
        d = My_AES_CBC(self.Aes_key, self.Aes_IV).decrypt(encrypted_text)
        return d
    
    
    # 获取注册码，验证成功后生成注册文件
    def regist(self):
        machine_code = self.getMachineCode()
        print('请发送', machine_code, '联系呆哥微信：guixiao198881，获取注册码')
        key_code = input('请输入激活码:')
        if key_code:
            try:
                register_str = base64.b32decode(key_code)
                decode_key_data = json.loads(self.Decrypt(register_str))
            except:
                print("激活码错误，请重新输入！")
                return self.regist()
            
            active_code = decode_key_data["code"].upper()
            end_timestamp = decode_key_data["endTs"]
        
            encrypt_code = self.Encrypt(machine_code)
            md5_code = hashlib.md5(encrypt_code).hexdigest().upper()

            if md5_code != active_code:
                print("激活码错误，请重新输入！")
                return self.regist()
            
            curTs = int(time.time())
            if curTs >= end_timestamp:
                print("激活码已过期，请重新输入！")
                return self.regist()
                
            time_local = time.localtime(end_timestamp)
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            print("激活成功！有效期至 %s" %dt)
            with open('register.bin', 'wb') as f:
                f.write(register_str)
            return True
        else:
            return False
 
 
    # 打开程序先调用注册文件，比较注册文件中注册码与此时的硬件信息编码后是否一致
    def checkAuthored(self):
    
        if not os.path.exists("register.bin"):
            return False

        with open("register.bin", "rb") as f:
            key_code = f.read()
            
        if not key_code:
            return False
            
        # 本地计算激活码
        machine_code = self.getMachineCode()
        encrypt_code = self.Encrypt(machine_code)
        md5_code = hashlib.md5(encrypt_code).hexdigest().upper()

        # 解析激活码和到期时间
        try:
            decode_key_data = json.loads(self.Decrypt(key_code))
            active_code = decode_key_data["code"].upper()
            end_timestamp = decode_key_data["endTs"]
            curTs = int(time.time())
        except:
            print("激活码失效，请重新激活！")
            return False

        # 校验
        if md5_code != active_code:
            print("激活码失效，请重新激活！")
            return False
        
        curTs = int(time.time())
        if curTs >= end_timestamp:
            print("激活码失效，请重新激活！")
            return False

        return True


def 合成照片(original_image,file_path,补充,自动):
    # 打开原始图片
    #original_image = Image.open("3-整体图【自己提供】.jpg")  # 替换为你的原始图片路径

    if(自动 == "A3"):
        #A3画进行裁剪
        叠加行 = 6
        叠加列 = 9
    elif(自动 == "A4"):
        #A4画进行裁剪 
        叠加行 = 5
        叠加列 = 6
    else:
        叠加行 = int(text_entry叠加行.get())
        叠加列 = int(text_entry叠加列.get())
    
    # 获取原始图片的宽度和高度
    width, height = original_image.size

    # 创建一个新的图片，宽度为4倍原始图片宽度，高度为3倍原始图片高度
    new_width = width * 叠加行
    new_height = height * 叠加列
    new_image = Image.new("RGB", (new_width, new_height))

    # # 创建一个用于绘制的对象
    # draw = ImageDraw.Draw(new_image)

    # 创建一个新的图像，使用RGBA模式，其中"A"代表透明度
    new_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

    # 将原始图片复制到新图片的不同位置
    for row in range(叠加列):
        for col in range(叠加行):
            x_offset = col * width
            y_offset = row * height
            new_image.paste(original_image, (x_offset, y_offset))

    if(自动 == "A3"):
        #A3画进行裁剪
        cropped_image = new_image.crop((0, 0, 3508, 4961))
    elif(自动 == "A4"):
        #A4画进行裁剪
        cropped_image = new_image.crop((0, 0, 2479, 3508))
    else:
        cropped_image = new_image

    # 保存新图片
    cropped_image.save(名称处理(file_path,补充))  # 替换为你希望保存的新图片路径
    进度_label.config(text=f"处理进度：{补充}已经处理完成",font=("Helvetica", 20), fg="red")
    return cropped_image

def 分辨率调整到300(original_image):
    # 打开原始图片
    #original_image = Image.open("3-整体图【自己提供】.jpg")  # 替换为你的原始图片路径

    # 定义目标分辨率（例如300 dpi）
    target_dpi = 300

    # 计算目标像素尺寸
    target_width = int(original_image.width * target_dpi / 72)
    target_height = int(original_image.height * target_dpi / 72)

    # 重新采样图像以增加像素密度
    resized_image = original_image.resize((target_width, target_height), Image.ANTIALIAS)

    # 保存处理后的高分辨率图片
    #resized_image.save("3-整体图【自己提供】-高分辨率.png", dpi=(target_dpi, target_dpi))  # 替换为你希望保存的高分辨率图片路径

    return resized_image

def 无缝贴图():

    # 打开原始图片
    original_image = Image.open("3-整体图【自己提供】-高分辨率.png")  # 替换为你的原始图片路径

    # 获取原始图片的宽度和高度
    original_width, original_height = original_image.size

    # 计算裁剪后的宽度和高度（取中心的0.8倍大小）
    crop_width = int(original_width *1 )
    crop_height = int(original_height * 1 )

    # 计算裁剪的起始坐标，以使图片保持在中心
    x_start = (original_width - crop_width) // 2
    y_start = (original_height - crop_height) // 2
    x_end = x_start + crop_width
    y_end = y_start + crop_height

    # 对原始图片进行裁剪
    cropped_image = original_image.crop((x_start, y_start, x_end, y_end))

    # 定义生成的无缝贴图的大小
    seamless_width = 6000
    seamless_height = 9000

    # 创建一个新的画布，用于生成无缝贴图
    seamless_image = Image.new("RGB", (seamless_width, seamless_height))

    # 计算在生成的贴图中平铺裁剪后的图片的次数
    x_tiles = seamless_width // crop_width + 1
    y_tiles = seamless_height // crop_height + 1

    # 在新画布上平铺裁剪后的图片，以生成无缝贴图
    for x in range(x_tiles):
        for y in range(y_tiles):
            seamless_image.paste(cropped_image, (x * crop_width, y * crop_height))

    # 裁剪生成的无缝贴图为指定的大小
    seamless_image = seamless_image.crop((0, 0, seamless_width, seamless_height))

    # 保存生成的无缝贴图
    seamless_image.save("4-叠加名字【生成后期用】.png")  # 替换为你希望保存的无缝贴图路径

def 手写图处理(original_image,file_path,补充):
    # 打开原始图片
    #original_image = Image.open("1-中间图【自己提供】.jpg")  # 替换为你的原始图片路径

    # 获取原始图片的宽度和高度
    original_width, original_height = original_image.size

    # 计算裁剪后的宽度和高度（竖直和水平中间分成4等份）
    crop_width = original_width // 2
    crop_height = original_height // 2

    # 分割原始图片为四个部分
    top_left = original_image.crop((0, 0, crop_width, crop_height))
    top_right = original_image.crop((crop_width, 0, original_width, crop_height))
    bottom_left = original_image.crop((0, crop_height, crop_width, original_height))
    bottom_right = original_image.crop((crop_width, crop_height, original_width, original_height))

    # 交换左上角和右下角的部分
    top_left, bottom_right = bottom_right, top_left

    # 交换左下角和右上角的部分
    bottom_left, top_right = top_right, bottom_left

    # 创建一个新的画布，用于组合四个部分
    new_width = original_width + (crop_width if original_width % 2 == 1 else 0)  # 调整新画布宽度
    new_height = original_height + (crop_height if original_height % 2 == 1 else 0)  # 调整新画布高度

    # 创建一个新的图像，使用RGBA模式，其中"A"代表透明度
    new_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

    # 将四个部分重新组合成新的图
    new_image.paste(top_left, (0, 0))
    new_image.paste(top_right, (crop_width, 0))
    new_image.paste(bottom_left, (0, crop_height))
    new_image.paste(bottom_right, (crop_width, crop_height))

    # 保存生成的新图
    new_image.save(名称处理(file_path,补充))  # 替换为你希望保存的新图片路径
    进度_label.config(text=f"处理进度：{补充}已经处理完成",font=("Helvetica", 20), fg="red")
    return new_image

def 改变图片颜色(original_image,file_path,补充):
    # 打开原始图片
    #original_image = Image.open("4-叠加名字【生成后期用】.png")  # 替换为你的原始图片路径

    # 获取原始图片的宽度和高度
    original_width, original_height = original_image.size

    # 定义要替换的颜色范围（在这里示例为将灰色替换为红色）
    # 你可以根据需要修改这些颜色范围
    lower_color = (0, 0, 0)  # 最小颜色值（黑色）
    upper_color = (100, 100, 100)  # 最大颜色值（灰色）

    print(皮肤像素点)
    # 定义要替换的目标颜色（将其替换为红色）
    replacement_color = 皮肤像素点  # 红色

    # 处理每个像素，将在指定颜色范围内的像素替换为红色
    for x in range(original_width):
        for y in range(original_height):
            pixel_color = original_image.getpixel((x, y))
            if all(lower <= value <= upper for value, lower, upper in zip(pixel_color, lower_color, upper_color)):
                original_image.putpixel((x, y), replacement_color)

    # 保存处理后的图片
    original_image.save(名称处理(file_path,补充))  # 替换为你希望保存的处理后的图片路径
    进度_label.config(text=f"处理进度：{补充}已经处理完成",font=("Helvetica", 20), fg="red")

    return  original_image

def 模糊照片(image,file_path,补充):
    # 打开图片
    #image = Image.open('0-初始照片.jpg')

    # 设置模糊半径，增加半径以增加模糊程度
    blur_radius = int(text_entry模糊系数.get())

    # 将图片模糊化，使用指定的半径
    blurred_image = image.filter(ImageFilter.GaussianBlur(blur_radius))

    # 保存模糊化后的图片
    blurred_image.save(名称处理(file_path,补充))
    进度_label.config(text=f"处理进度：{补充}已经处理完成",font=("Helvetica", 20), fg="red")

    return blurred_image

def 黑白照片(image,file_path,补充):
    # 打开图片
    #image = Image.open('6-模糊照片【后期用】.png')

    # 将图片转换为黑白
    black_and_white_image = image.convert('L')

    # 保存黑白图片
    black_and_white_image.save(名称处理(file_path,补充))
    进度_label.config(text=f"处理进度：{补充}已经处理完成",font=("Helvetica", 20), fg="red")


    return black_and_white_image

def 名称处理(original_string,插入部分):

    # 找到文件名的位置，即最后一个点的位置
    dot_index = original_string.rfind(".")

    # 使用切片将字符串分成两部分，然后插入文本
    new_string = original_string[:dot_index] + 插入部分 + original_string[dot_index:]

    return new_string

def step_1():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file_path:
            # 打开选择的图片
            image = Image.open(file_path)
            image = 手写图处理(image,file_path,"【四周图】")
            # 将图片显示在界面上
            # 检查图片宽度是否大于100像素
            if image.width > 500:
                # 对图片进行缩放，限制宽度为100像素
                image = image.resize((500, int(image.height * (500 / image.width))))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.photo = photo

def step_2():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file_path:
            # 打开选择的图片
            image = Image.open(file_path)
            #image = 分辨率调整到300(image)
            image = 合成照片(image,file_path,"【图片叠加】","无")
            # 将图片显示在界面上
            # 检查图片宽度是否大于100像素
            if image.width > 500:
                # 对图片进行缩放，限制宽度为100像素
                image = image.resize((500, int(image.height * (500 / image.width))))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.photo = photo

def step_A4():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file_path:
            # 打开选择的图片
            image = Image.open(file_path)
            #image = 分辨率调整到300(image)
            image = 合成照片(image,file_path,"【A4图片叠加】","A4")
            # 将图片显示在界面上
            # 检查图片宽度是否大于100像素
            if image.width > 500:
                # 对图片进行缩放，限制宽度为100像素
                image = image.resize((500, int(image.height * (500 / image.width))))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.photo = photo

def step_A3():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file_path:
            # 打开选择的图片
            image = Image.open(file_path)
            #image = 分辨率调整到300(image)
            image = 合成照片(image,file_path,"【A3图片叠加】","A3")
            # 将图片显示在界面上
            # 检查图片宽度是否大于100像素
            if image.width > 500:
                # 对图片进行缩放，限制宽度为100像素
                image = image.resize((500, int(image.height * (500 / image.width))))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.photo = photo

def step_3():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file_path:
            # 打开选择的图片
            进度_label.config(text=f"处理进度：皮肤颜色正在处理",font=("Helvetica", 20), fg="red")
            image = Image.open(file_path)
            image = 改变图片颜色(image,file_path,"【皮肤颜色】")
            # 将图片显示在界面上
            # 检查图片宽度是否大于100像素
            if image.width > 500:
                # 对图片进行缩放，限制宽度为100像素
                image = image.resize((500, int(image.height * (500 / image.width))))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.photo = photo

def 获取像素(event):
    x, y = event.x, event.y
    global 皮肤像素点
    global image
    皮肤像素点 = image.getpixel((x, y))
    color_label.config(text=f"像素颜色：{皮肤像素点}")

def 获取皮肤颜色():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
    if file_path:
        global image
        image = Image.open(file_path)

        # 检查图片宽度是否大于100像素
        if image.width > 500:
            # 对图片进行缩放，限制宽度为100像素
            image = image.resize((500, int(image.height * (500 / image.width))))
        photo = ImageTk.PhotoImage(image)
        image_label.config(image=photo)
        image_label.photo = photo

def step_4():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file_path:
            # 打开选择的图片
            image = Image.open(file_path)
            image = 模糊照片(image,file_path,"【原图模糊】")

            # 将图片显示在界面上
            # 检查图片宽度是否大于100像素
            if image.width > 500:
                # 对图片进行缩放，限制宽度为100像素
                image = image.resize((500, int(image.height * (500 / image.width))))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.photo = photo

def step_5():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file_path:
            # 打开选择的图片
            image = Image.open(file_path)
            image = 黑白照片(image,file_path,"【黑白】")
            模糊照片(image,file_path,"【黑白】【模糊】")

            # 将图片显示在界面上
            # 检查图片宽度是否大于100像素
            if image.width > 500:
                # 对图片进行缩放，限制宽度为100像素
                image = image.resize((500, int(image.height * (500 / image.width))))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.photo = photo

if __name__ == '__main__':
    register = Register()
    while(not register.checkAuthored()):
        register.regist()

# 创建主窗口
window = tk.Tk()
window.title("名字画辅助软件【呆哥开发】")
window.geometry("700x1000")

# 创建一个函数，用于打开文件对话框并选择照片

进度_label = tk.Label(window, text="处理进度：还未开始处理",font=("Helvetica", 20), fg="red")
进度_label.pack(side=tk.TOP,pady=10)

# 创建三个标签并使用不同的pack选项排列它们
button1 = tk.Button(window, text="第一步【名字预处理】", command=step_1,width=30,font=("Helvetica", 15), fg="black")
button1.pack(side=tk.TOP, padx=10, pady=10, anchor=tk.W)

叠加_frame = tk.Frame(window)
叠加_frame.pack(side=tk.TOP,padx=10, pady=10,anchor=tk.W)

button2 = tk.Button(叠加_frame, text="第二步【名字叠加处理】", command=step_2,width=30,font=("Helvetica", 15), fg="black")
button2.pack(side=tk.LEFT,  padx=10, pady=10, anchor=tk.W)

text_entry叠加行 = tk.Entry(叠加_frame, width=5,font=("Helvetica", 15), fg="red")
text_entry叠加行.pack(side=tk.LEFT, padx=10, pady=10)
text_entry叠加行.insert(0, "4")

text_label行 = tk.Label(叠加_frame, text="行",width=5,font=("Helvetica", 15), fg="blue")
text_label行.pack(side=tk.LEFT, padx=10, pady=10)

text_entry叠加列 = tk.Entry(叠加_frame, width=5,font=("Helvetica", 15), fg="red")
text_entry叠加列.pack(side=tk.LEFT, padx=10, pady=10)
text_entry叠加列.insert(0, "6")

text_label列 = tk.Label(叠加_frame, text="列",width=5,font=("Helvetica", 15), fg="blue")
text_label列.pack(side=tk.LEFT, padx=10, pady=10)

一键_frame = tk.Frame(window)
一键_frame.pack(side=tk.TOP,padx=10, pady=10,anchor=tk.W)

button_A3 = tk.Button(一键_frame, text="【一键名字A3叠加处理】", command=step_A3,width=30,font=("Helvetica", 15), fg="black")
button_A3.pack(side=tk.LEFT,padx=10, pady=10, anchor=tk.W)

button_A4 = tk.Button(一键_frame, text="【一键名字A4叠加处理】", command=step_A4,width=30,font=("Helvetica", 15), fg="black")
button_A4.pack(side=tk.LEFT,padx=10, pady=10, anchor=tk.W)

皮肤_frame = tk.Frame(window)
皮肤_frame.pack(side=tk.TOP,padx=10, pady=10,anchor=tk.W)


button3 = tk.Button(皮肤_frame, text="第三步【名字皮肤处理】", command=step_3,width=30,font=("Helvetica", 15), fg="black")
button3.pack(side=tk.LEFT,padx=10, pady=10, anchor=tk.W)

open_button = tk.Button(皮肤_frame, text="获取皮肤颜色", command=获取皮肤颜色,font=("Helvetica", 15), fg="black")
open_button.pack(side=tk.LEFT,pady=10)

color_label = tk.Label(皮肤_frame, text="像素颜色：",font=("Helvetica", 15), fg="black")
color_label.pack(side=tk.LEFT,pady=10)

模糊_frame = tk.Frame(window)
模糊_frame.pack(side=tk.TOP,padx=10, pady=10,anchor=tk.W)

button4 = tk.Button(模糊_frame, text="第四步【相片模糊处理】", command=step_4,width=30,font=("Helvetica", 15), fg="black")
button4.pack(side=tk.LEFT, padx=10, pady=10, anchor=tk.W)

text_entry模糊系数 = tk.Entry(模糊_frame, width=5,font=("Helvetica", 15), fg="red")
text_entry模糊系数.pack(side=tk.LEFT, padx=10, pady=10)
text_entry模糊系数.insert(0, "8")

# 创建文本标签
text_label = tk.Label(模糊_frame, text="【1-10的数字】模糊系数",width=50,font=("Helvetica", 15), fg="blue")
text_label.pack(side=tk.LEFT, padx=10, pady=10)

button5 = tk.Button(window, text="第五步【相片黑白处理】", command=step_5,width=30,font=("Helvetica", 15), fg="black")
button5.pack(side=tk.TOP, padx=10, pady=10, anchor=tk.W)

# 创建一个标签，用于显示选定的图片
image_label = tk.Label(window)
image_label.pack()

image_label.bind("<Button-1>", 获取像素)

# 启动主循环
window.mainloop()







