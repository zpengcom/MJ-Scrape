# 依赖说明：
# 需要安装以下Python库：
# 1. requests - 用于下载图片
#    安装命令: pip install requests
# 2. tqdm - 用于显示下载进度条
#    安装命令: pip install tqdm
# 标准库(os, csv, urllib.parse, argparse, concurrent.futures等)无需额外安装
# 可选依赖:
# 1. curl - 作为下载方式之一 (用户可选)
#
# ========================================================================
# MJ-CSV-DL.py - Midjourney CSV下载工具
# ========================================================================
# 脚本用途:
#   该脚本用于处理包含Midjourney任务数据的CSV文件，提取并保存文本提示(Prompt)为txt文件，
#   同时下载相应的图片。支持单个CSV文件处理和批量目录处理。
#
# 主要功能:
#   1. 从CSV提取Prompt文本并保存为txt文件，文件命名统一采用扩展模式的命名方式（例如 任务ID_0.txt）
#   2. 下载CSV中的图片链接指向的图片，图片文件名与文本文件对应（例如 任务ID_0.png）
#   3. 支持单个CSV文件或整个目录的批量处理
#   4. 支持多线程并行下载，提高处理速度
#   5. 提供四种下载方式供用户选择（默认使用curl方式），用户可通过参数或交互提示选择方式
#   6. 【扩展模式】：在扩展模式下，每个任务构造0_0至0_3四个下载任务（命名如 taskID_0、taskID_1...），
#      如果某个图片下载失败，则对应的txt文件不生成；扩展模式下最多重试1次，普通模式下重试2次。
#   7. 【优化】：如果保存的目录中已存在要下载的图片和文本文件，则自动略过不处理。
#
# 命令行参数说明:
#   python MJ-CSV-DL.py [input_path] [output_dir] [选项]
#   python MJ-CSV-DL.py  # 不带参数时默认进入交互模式
#
#   位置参数:
#     input_path            CSV文件或包含CSV文件的目录路径
#     output_dir            文件(文本和图片)保存目录
#
#   可选参数:
#     -h, --help            显示帮助信息并退出
#     --test-url URL        测试下载单个图片URL
#     --test-task-url URL   测试下载时使用的任务URL（用于浏览器模拟下载）
#     --test-output DIR     测试下载图片的保存目录
#     --check-curl          检查curl是否已安装
#     --threads N, -t N     并行下载的线程数 (默认: 4)
#     --extended            启用扩展模式下载多个图片（构造0_0至0_3）
#     --method METHOD       选择下载方式，可选值：curl, browser, requests, urllib (默认: curl)
#
# 使用示例:
#   1. 处理单个CSV文件（普通模式，生成 taskID_0.xxx）:
#      python MJ-CSV-DL.py path/to/file.csv path/to/output --method curl
#
#   2. 批量处理目录中的所有CSV文件（扩展模式，生成 taskID_0 ～ taskID_3）:
#      python MJ-CSV-DL.py path/to/directory path/to/output --extended --method curl
#
#   3. 使用8个线程进行并行下载:
#      python MJ-CSV-DL.py path/to/file.csv path/to/output --threads 8 --method curl
#
#   4. 测试下载单个图片:
#      python MJ-CSV-DL.py --test-url https://cdn.midjourney.com/xxx/0_0.png --method curl
#
#   5. 检查curl是否已安装:
#      python MJ-CSV-DL.py --check-curl
#
# CSV文件格式要求:
#   CSV文件必须包含以下字段:
#   - 'Prompt': 文本提示内容
#   - '任务id'或'任务ID': 用于文件命名的任务标识符
#   - '图片链接': 要下载的图片URL
#
#   可选字段:
#   - '任务链接': 任务页面URL，用于增强图片下载功能
#
# 注意事项:
#   1. 扩展模式下针对下载失败的图片最多重试1次，且下载失败时不生成对应的txt文件
#   2. 普通模式下下载失败最多重试2次
#   3. 大量图片下载时建议使用多线程(--threads参数)提高效率
#   4. 字段名区分大小写，但'任务id'和'任务ID'都被支持
#   5. 如果保存的目录中已存在要下载的图片和文本文件，则自动略过不处理
# ========================================================================

import os
import csv
import requests
import argparse
import random
import traceback
import time
import urllib.request
import subprocess
import shutil
import platform
import sys
import concurrent.futures
from tqdm import tqdm
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

def get_random_user_agent():
    """返回一个随机的User-Agent字符串"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    ]
    return random.choice(user_agents)

def get_browser_headers(url):
    """返回模拟浏览器的请求头"""
    parsed_url = urlparse(url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": domain,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site",
    }
    return headers

def get_extended_url(original_url, index):
    """
    根据原始图片链接构造扩展模式下的链接，
    将链接中最后一个下划线后的数字替换为 index，
    如：https://.../0_0.png 生成 https://.../0_1.png 等
    """
    base, ext = os.path.splitext(original_url)
    pos = base.rfind('_')
    if pos == -1:
        return f"{base}_{index}{ext}"
    else:
        return f"{base[:pos+1]}{index}{ext}"

def download_image_with_requests(url, save_path, max_retries=2):
    """使用requests库下载图片"""
    headers = get_browser_headers(url)
    retry_count = 0
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                time.sleep(random.uniform(1.0, 3.0))
            session = requests.Session()
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            session.get(domain, headers=headers, timeout=10)
            response = session.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith(('image/', 'application/octet-stream')):
                print(f"警告: 响应不是图片类型 ({content_type}), 但仍尝试保存")
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"成功下载图片(requests方式): {save_path}")
            return True
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                print(f"下载失败(requests方式), 重试 ({retry_count}/{max_retries}): {str(e)}")
            else:
                print(f"下载失败(requests方式), 已达最大重试次数: {str(e)}")
                return False

def download_image_with_urllib(url, save_path, max_retries=2):
    """使用urllib库下载图片"""
    headers = get_browser_headers(url)
    retry_count = 0
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                time.sleep(random.uniform(1.0, 3.0))
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status != 200:
                    raise HTTPError(url, response.status, "HTTP Error", response.headers, None)
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith(('image/', 'application/octet-stream')):
                    print(f"警告: 响应不是图片类型 ({content_type}), 但仍尝试保存")
                with open(save_path, 'wb') as f:
                    f.write(response.read())
            print(f"成功下载图片(urllib方式): {save_path}")
            return True
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                print(f"下载失败(urllib方式), 重试 ({retry_count}/{max_retries}): {str(e)}")
            else:
                print(f"下载失败(urllib方式), 已达最大重试次数: {str(e)}")
                return False

def download_image_with_curl(url, save_path, max_retries=2):
    """使用curl命令下载图片"""
    curl_path = shutil.which("curl")
    if not curl_path:
        print("未找到curl命令，请安装curl后再试")
        return False
    headers = get_browser_headers(url)
    retry_count = 0
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                time.sleep(random.uniform(1.0, 3.0))
            temp_file = f"{save_path}.tmp"
            header_args = []
            for key, value in headers.items():
                if key != "User-Agent":
                    header_args.extend(["-H", f"{key}: {value}"])
            cmd = [curl_path, "-s", "-S", "--fail", "-L",
                   "--connect-timeout", "15",
                   "--max-time", "30",
                   "-A", user_agent,
                   "-o", temp_file] + header_args + [url]
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                subprocess.run(cmd, startupinfo=startupinfo, check=True, stderr=subprocess.PIPE)
            else:
                subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                if os.path.exists(save_path):
                    os.remove(save_path)
                os.rename(temp_file, save_path)
                print(f"成功下载图片(curl方式): {save_path}")
                return True
            else:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise Exception("下载文件为空")
        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            retry_count += 1
            stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
            if retry_count <= max_retries:
                print(f"下载失败(curl方式), 重试 ({retry_count}/{max_retries}): 错误码 {e.returncode}, {stderr}")
            else:
                print(f"下载失败(curl方式), 已达最大重试次数: 错误码 {e.returncode}, {stderr}")
                return False
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            retry_count += 1
            if retry_count <= max_retries:
                print(f"下载失败(curl方式), 重试 ({retry_count}/{max_retries}): {str(e)}")
            else:
                print(f"下载失败(curl方式), 已达最大重试次数: {str(e)}")
                return False

def download_image_with_browser_simulation(image_url, task_url, save_path, max_retries=2):
    """通过访问任务URL获取认证信息后下载图片"""
    if not task_url:
        print("无法使用浏览器模拟方式：缺少任务URL")
        return False
    print(f"尝试使用浏览器模拟方式下载: {image_url}")
    print(f"通过任务链接: {task_url}")
    headers = get_browser_headers(task_url)
    retry_count = 0
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                time.sleep(random.uniform(1.5, 4.0))
            session = requests.Session()
            print("正在访问任务页面获取认证信息...")
            task_response = session.get(task_url, headers=headers, timeout=15)
            task_response.raise_for_status()
            print("正在使用获取的认证信息下载图片...")
            img_headers = get_browser_headers(image_url)
            img_headers['Referer'] = task_url
            response = session.get(image_url, headers=img_headers, stream=True, timeout=15)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith(('image/', 'application/octet-stream')):
                print(f"警告: 响应不是图片类型 ({content_type}), 但仍尝试保存")
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"成功下载图片(浏览器模拟方式): {save_path}")
            return True
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                print(f"下载失败(浏览器模拟方式), 重试 ({retry_count}/{max_retries}): {str(e)}")
            else:
                print(f"下载失败(浏览器模拟方式), 已达最大重试次数: {str(e)}")
                return False

def download_image(url, save_path, task_url=None, max_retries=2, method="curl"):
    """根据用户选择的方式下载图片，不进行依次尝试"""
    print(f"正在下载图片: {url}")
    if method == "curl":
        return download_image_with_curl(url, save_path, max_retries)
    elif method == "browser":
        return download_image_with_browser_simulation(url, task_url, save_path, max_retries)
    elif method == "requests":
        return download_image_with_requests(url, save_path, max_retries)
    elif method == "urllib":
        return download_image_with_urllib(url, save_path, max_retries)
    else:
        print("不支持的下载方式")
        return False

def download_worker(task):
    """
    线程工作函数，任务元组包含：
    (image_url, image_path, task_url, task_id, prompt_text, extended_mode, method)
    扩展模式下重试次数设置为1，其它模式下为2。
    如果图片和文本文件已存在，则跳过处理；下载成功后写入对应的txt文件，下载失败则不生成txt。
    """
    image_url, image_path, task_url, task_id, prompt_text, extended_mode, download_method = task
    txt_path = os.path.splitext(image_path)[0] + ".txt"
    
    # 检查图片和文本文件是否都已存在
    if os.path.exists(image_path) and os.path.exists(txt_path):
        print(f"跳过已存在的文件: {image_path} 和 {txt_path}")
        return {"task_id": task_id, "image_url": image_url, "image_path": image_path, "success": True}
    
    
    # 如果图片存在但文本文件不存在，仅生成文本文件
    elif os.path.exists(image_path) and not os.path.exists(txt_path):
        print(f"图片已存在，仅生成文本文件: {txt_path}")
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(prompt_text)
            print(f"成功保存Prompt文本: {txt_path}")
        except Exception as e:
            print(f"保存Prompt文本失败 ({task_id}): {str(e)}")
        return {"task_id": task_id, "image_url": image_url, "image_path": image_path, "success": True}
    
    # 下载图片并生成文本文件
    else:
        retries = 1 if extended_mode else 2
        success = download_image(image_url, image_path, task_url, max_retries=retries, method=download_method)
        if success:
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(prompt_text)
                print(f"成功保存Prompt文本: {txt_path}")
            except Exception as e:
                print(f"保存Prompt文本失败 ({task_id}): {str(e)}")
        else:
            if os.path.exists(txt_path):
                os.remove(txt_path)
            print(f"图片下载失败，未生成文本文件: {txt_path}")
        return {"task_id": task_id, "image_url": image_url, "image_path": image_path, "success": success}


def process_csv_file(csv_path, output_dir, num_threads=4, extended_mode=False, method="curl"):
    """
    处理单个CSV文件：
      - 提取每行的任务ID、Prompt和图片链接
      - 构造下载任务，文件命名统一为 <任务ID>_N.xxx（普通模式下N固定为0）
      - 下载成功后在对应图片同名位置生成txt文件；下载失败则不生成txt文件
    """
    os.makedirs(output_dir, exist_ok=True)
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)
            prompt_field = 'Prompt'
            if prompt_field not in reader.fieldnames:
                print(f"错误: CSV文件 {csv_path} 缺少必要字段 'Prompt'")
                return
            if '图片链接' not in reader.fieldnames:
                print(f"错误: CSV文件 {csv_path} 缺少必要字段 '图片链接'")
                return
            task_id_field = '任务id' if '任务id' in reader.fieldnames else '任务ID'
            if task_id_field not in reader.fieldnames:
                print(f"错误: CSV文件 {csv_path} 缺少必要字段 '任务id' 或 '任务ID'")
                return
            task_url_field = '任务链接' if '任务链接' in reader.fieldnames else None
            
            rows = list(reader)
            download_tasks = []
            for i, row in enumerate(rows):
                task_id = ''.join(c for c in row[task_id_field] if c.isalnum() or c in '._- ') or f"task_{i+1}"
                prompt_text = row[prompt_field].strip()
                image_url = row['图片链接'].strip()
                task_url = row[task_url_field].strip() if task_url_field and task_url_field in row else None
                if not image_url:
                    continue
                if extended_mode:
                    for idx in range(4):
                        new_task_id = f"{task_id}_{idx}"
                        extended_image_url = get_extended_url(image_url, idx)
                        image_path = os.path.join(output_dir, f"{new_task_id}.png")
                        download_tasks.append((extended_image_url, image_path, task_url, new_task_id, prompt_text, True, method))
                else:
                    new_task_id = f"{task_id}_0"
                    image_path = os.path.join(output_dir, f"{new_task_id}.png")
                    download_tasks.append((image_url, image_path, task_url, new_task_id, prompt_text, False, method))
            
            total_tasks = len(download_tasks)
            if total_tasks > 0:
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                    with tqdm(total=total_tasks, desc="下载进度", unit="张") as progress_bar:
                        future_to_task = {executor.submit(download_worker, task): i for i, task in enumerate(download_tasks)}
                        successful_downloads = 0
                        for future in concurrent.futures.as_completed(future_to_task):
                            result = future.result()
                            if result["success"]:
                                successful_downloads += 1
                            progress_bar.update(1)
                print(f"\n图片下载完成: 成功 {successful_downloads}/{total_tasks} 张")
            else:
                print("没有找到需要下载的图片链接")
    except Exception as e:
        print(f"处理CSV文件时出错: {str(e)}")

def process_directory(input_dir, output_dir, num_threads=4, extended_mode=False, method="curl"):
    """处理目录中的所有CSV文件"""
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.csv'):
            csv_path = os.path.join(input_dir, filename)
            print(f"\n正在处理: {csv_path}")
            process_csv_file(csv_path, output_dir, num_threads, extended_mode, method)

def process_input(input_path, output_dir, num_threads=4, extended_mode=False, method="curl"):
    """根据输入路径类型处理文件或目录"""
    if os.path.isfile(input_path) and input_path.lower().endswith('.csv'):
        process_csv_file(input_path, output_dir, num_threads, extended_mode, method)
    elif os.path.isdir(input_path):
        process_directory(input_path, output_dir, num_threads, extended_mode, method)
    else:
        print("错误: 输入路径不是CSV文件也不是目录！")
        
        
def main_interactive():
    """交互式模式的主函数"""
    print("=" * 80)
    print("MJ CSV下载工具 - 交互模式")
    print("=" * 80)
    print("\n完整使用提示：")
    print("  脚本用途:")
    print("    该脚本用于处理包含Midjourney任务数据的CSV文件，提取并保存文本提示(Prompt)为txt文件，")
    print("    同时下载相应的图片。支持单个CSV文件处理和批量目录处理。")
    print("\n  主要功能:")
    print("    1. 从CSV提取Prompt文本并保存为txt文件，文件命名统一采用扩展模式的命名方式（例如 任务ID_0.txt）")
    print("    2. 下载CSV中的图片链接指向的图片，图片文件名与文本文件对应（例如 任务ID_0.png）")
    print("    3. 支持单个CSV文件或整个目录的批量处理")
    print("    4. 支持多线程并行下载，提高处理速度")
    print("    5. 提供四种下载方式供用户选择（默认使用curl方式），用户可通过参数或交互提示选择方式")
    print("    6. 【扩展模式】：在扩展模式下，每个任务构造0_0至0_3四个下载任务（命名如 taskID_0、taskID_1...），")
    print("       如果某个图片下载失败，则对应的txt文件不生成；扩展模式下最多重试1次，普通模式下重试2次。")
    print("    7. 【优化】：如果保存的目录中已存在要下载的图片和文本文件，则自动略过不处理。")
    print("\n  使用步骤：")
    print("    1. 输入CSV文件路径或目录路径")
    print("    2. 输入文件保存目录")
    print("    3. 选择是否启用扩展模式（下载多个图片）")
    print("    4. 选择下载方式（curl, browser, requests, urllib）")
    print("\n  CSV文件格式要求:")
    print("    CSV文件必须包含以下字段:")
    print("    - 'Prompt': 文本提示内容")
    print("    - '任务id'或'任务ID': 用于文件命名的任务标识符")
    print("    - '图片链接': 要下载的图片URL")
    print("    可选字段:")
    print("    - '任务链接': 任务页面URL，用于增强图片下载功能")
    print("\n  注意事项:")
    print("    1. 扩展模式下针对下载失败的图片最多重试1次，且下载失败时不生成对应的txt文件")
    print("    2. 普通模式下下载失败最多重试2次")
    print("    3. 大量图片下载时建议使用多线程（默认4个线程）提高效率")
    print("    4. 字段名区分大小写，但'任务id'和'任务ID'都被支持")
    print("    5. 如果保存的目录中已存在要下载的图片和文本文件，则自动略过不处理")
    print("=" * 80)
    while True:
        input_path = input("请输入CSV文件路径或目录路径: ").strip()
        if os.path.exists(input_path):
            break
        print("路径不存在，请重新输入！")
    while True:
        output_dir = input("请输入文件保存目录: ").strip()
        try:
            os.makedirs(output_dir, exist_ok=True)
            break
        except Exception as e:
            print(f"无法创建目录: {str(e)}，请重新输入！")
    
    ext_input = input("是否启用扩展模式（下载多个图片）？(y/n 默认n): ").strip().lower()
    extended_mode = ext_input == 'y'
    
    print("\n请选择下载方式：")
    print("  1. curl      (使用 curl 命令下载，默认)")
    print("  2. browser   (通过浏览器模拟方式下载)")
    print("  3. requests  (使用 Python requests 库下载)")
    print("  4. urllib    (使用 Python urllib 库下载)")
    method_input = input("请输入对应的方式 (可直接输入名称或数字，默认: curl): ").strip().lower()
    if method_input in ["", "1", "curl"]:
        download_method = "curl"
    elif method_input in ["2", "browser"]:
        download_method = "browser"
    elif method_input in ["3", "requests"]:
        download_method = "requests"
    elif method_input in ["4", "urllib"]:
        download_method = "urllib"
    else:
        print("输入不合法，默认使用 curl")
        download_method = "curl"
    
    process_input(input_path, output_dir, 4, extended_mode, download_method)

def test_download_image(url, output_dir=None, task_url=None):
    """测试下载单个图片URL功能"""
    if not output_dir:
        output_dir = os.path.join(os.getcwd(), "test_images")
    os.makedirs(output_dir, exist_ok=True)
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    if not file_name:
        file_name = f"test_image_{int(time.time())}.png"
    if not os.path.splitext(file_name)[1]:
        file_name += ".png"
    save_path = os.path.join(output_dir, file_name)
    print(f"测试下载图片: {url}")
    if task_url:
        print(f"使用任务URL: {task_url}")
    print(f"保存路径: {save_path}")
    result = download_image(url, save_path)
    if result:
        print("✅ 测试成功: 图片已成功下载")
    else:
        print("❌ 测试失败: 无法下载图片")
    return result

def check_curl_installation():
    """检查curl是否已安装"""
    curl_path = shutil.which("curl")
    if curl_path:
        print(f"✅ curl已安装: {curl_path}")
        return True
    else:
        print("❌ curl未安装。建议安装curl以提高下载成功率。")
        if platform.system() == "Windows":
            print("  Windows安装方法: 例如使用Chocolatey: choco install curl")
        elif platform.system() == "Darwin":
            print("  macOS安装方法: brew install curl")
        elif platform.system() == "Linux":
            print("  Linux安装方法: sudo apt-get install curl 或 sudo yum install curl")
        return False

def main():
    """命令行模式的主函数"""
    parser = argparse.ArgumentParser(description="MJ CSV下载工具 - 处理CSV数据并下载图片")
    parser.add_argument('input_path', nargs='?', help='CSV文件或目录路径')
    parser.add_argument('output_dir', nargs='?', help='文件保存目录')
    parser.add_argument('--test-url', help='测试下载单个图片URL')
    parser.add_argument('--test-task-url', help='测试下载时使用的任务URL（用于浏览器模拟下载）')
    parser.add_argument('--test-output', help='测试下载图片的保存目录')
    parser.add_argument('--check-curl', action='store_true', help='检查curl是否已安装')
    parser.add_argument('--threads', '-t', type=int, default=4, help='并行下载的线程数 (默认: 4)')
    parser.add_argument('--interactive', action='store_true', help='使用交互式模式运行脚本')
    parser.add_argument('--extended', action='store_true', help='启用扩展模式下载多个图片（构造0_0至0_3）')
    parser.add_argument('--method', choices=["curl", "browser", "requests", "urllib"], default="curl",
                        help='选择下载方式 (默认: curl)')
    args = parser.parse_args()
    
    if args.check_curl:
        check_curl_installation()
        return
    if args.test_url:
        test_download_image(args.test_url, args.test_output, args.test_task_url)
    elif args.interactive:
        main_interactive()
    elif args.input_path and args.output_dir:
        input_path = args.input_path.strip()
        output_dir = args.output_dir.strip()
        if not os.path.exists(input_path):
            print(f"错误: 输入路径 '{input_path}' 不存在！")
            return
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"错误: 无法创建输出目录 '{output_dir}': {str(e)}")
            return
        process_input(input_path, output_dir, args.threads, args.extended, args.method)
    else:
        print("没有提供足够的命令行参数，默认进入交互模式...\n")
        main_interactive()

if __name__ == "__main__":
    main()
