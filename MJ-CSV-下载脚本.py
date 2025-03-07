# 依赖说明：
# 需要安装以下Python库：
# 1. requests - 用于下载图片
#    安装命令: pip install requests
# 2. tqdm - 用于显示下载进度条
#    安装命令: pip install tqdm
# 标准库(os, csv, urllib.parse, argparse, concurrent.futures等)无需额外安装
# 可选依赖:
# 1. curl - 作为备选图片下载方法 (如果前两种方法失败)
#
# ========================================================================
# MJ-CSV-DL.py - Midjourney CSV下载工具
# ========================================================================
# 脚本用途:
#   该脚本用于处理包含Midjourney任务数据的CSV文件，提取并保存文本提示(Prompt)为
#   txt文件，同时下载相应的图片。支持单个CSV文件处理和批量目录处理。
#
# 主要功能:
#   1. 从CSV提取Prompt文本并保存为txt文件，以任务ID命名
#   2. 下载CSV中的图片链接指向的图片，以任务ID命名
#   3. 支持单个CSV文件或整个目录的批量处理
#   4. 支持多线程并行下载，提高处理速度
#   5. 多种下载方法自动切换，提高下载成功率
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
#     --test-task-url URL   测试下载时使用的任务URL(用于浏览器模拟下载)
#     --test-output DIR     测试下载图片的保存目录
#     --check-curl          检查curl是否已安装
#     --threads N, -t N     并行下载的线程数(默认: 4)
#
# 使用示例:
#   1. 处理单个CSV文件:
#      python MJ-CSV-DL.py path/to/file.csv path/to/output
#
#   2. 批量处理目录中的所有CSV文件:
#      python MJ-CSV-DL.py path/to/directory path/to/output
#
#   3. 使用8个线程进行并行下载:
#      python MJ-CSV-DL.py path/to/file.csv path/to/output --threads 8
#
#   4. 测试下载单个图片:
#      python MJ-CSV-DL.py --test-url https://cdn.midjourney.com/xxx/0_0.png
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
#   1. 如果遇到下载失败，脚本会自动尝试多种下载方法
#   2. 推荐安装curl以提高下载成功率
#   3. 大量图片下载时建议使用多线程(--threads参数)提高效率
#   4. 字段名区分大小写，但'任务id'和'任务ID'都被支持
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
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        # Edge
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

def download_image_with_requests(url, save_path, max_retries=2):
    """使用requests库下载图片"""
    headers = get_browser_headers(url)
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # 添加一些随机延迟，避免请求过快
            if retry_count > 0:
                time.sleep(random.uniform(1.0, 3.0))
                
            # 创建session对象，保持cookie
            session = requests.Session()
            
            # 先访问域名首页获取cookies
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            session.get(domain, headers=headers, timeout=10)
            
            # 使用同一session下载图片
            response = session.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            # 检查响应是否是图片类型
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
                
            # 创建Request对象
            req = urllib.request.Request(url, headers=headers)
            
            # 打开连接并读取数据
            with urllib.request.urlopen(req, timeout=15) as response:
                # 检查状态码
                if response.status != 200:
                    raise HTTPError(url, response.status, "HTTP Error", response.headers, None)
                
                # 检查内容类型
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith(('image/', 'application/octet-stream')):
                    print(f"警告: 响应不是图片类型 ({content_type}), 但仍尝试保存")
                
                # 读取并保存数据
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
    # 确保curl命令存在
    curl_path = shutil.which("curl")
    if not curl_path:
        print("未找到curl命令，请安装curl后再试")
        return False
    
    headers = get_browser_headers(url)
    retry_count = 0
    
    # 使用成功验证过的User-Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                time.sleep(random.uniform(1.0, 3.0))
            
            # 设置临时文件名，以避免文件锁定问题
            temp_file = f"{save_path}.tmp"
            
            # 构建curl命令的头信息参数
            header_args = []
            for key, value in headers.items():
                if key != "User-Agent":  # 跳过User-Agent，将使用-A参数设置
                    header_args.extend(["-H", f"{key}: {value}"])
            
            # 构建curl命令，使用-A设置User-Agent
            cmd = [curl_path, "-s", "-S", "--fail", "-L", 
                   "--connect-timeout", "15", 
                   "--max-time", "30",
                   "-A", user_agent,  # 直接设置User-Agent
                   "-o", temp_file] + header_args + [url]
            
            # 如果是Windows系统，使用CREATE_NO_WINDOW标志以防止在Windows上显示控制台窗口
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                process = subprocess.run(cmd, startupinfo=startupinfo, 
                                        check=True, stderr=subprocess.PIPE)
            else:
                # 在Unix系统上运行
                process = subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            
            # 如果临时文件存在并且大小大于0，则重命名为目标文件
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
    """通过访问任务URL获取必要的认证信息，然后下载图片"""
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
                
            # 创建session对象，保持cookie
            session = requests.Session()
            
            # 先访问任务URL获取cookies和认证信息
            print(f"正在访问任务页面获取认证信息...")
            task_response = session.get(task_url, headers=headers, timeout=15)
            task_response.raise_for_status()
            
            # 使用相同的session下载图片
            print(f"正在使用获取的认证信息下载图片...")
            img_headers = get_browser_headers(image_url)
            # 设置Referer为任务URL
            img_headers['Referer'] = task_url
            
            response = session.get(image_url, headers=img_headers, stream=True, timeout=15)
            response.raise_for_status()
            
            # 检查响应是否是图片类型
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

def download_image(url, save_path, task_url=None):
    """下载图片并保存到指定路径，如果一种方式失败，尝试其他方式
    
    参数:
    url -- 图片URL
    save_path -- 图片保存路径
    task_url -- 可选的任务URL，用于浏览器模拟下载
    """
    print(f"正在下载图片: {url}")
    
    # 方式1: 优先使用curl命令下载（已被证明有效）
    print("尝试使用curl方式下载...")
    if download_image_with_curl(url, save_path):
        return True
    
    print("curl下载失败，尝试其他方式...")
    
    # 方式2: 使用任务URL的浏览器模拟方式下载（如果提供了任务URL）
    if task_url:
        print("尝试使用浏览器模拟方式下载...")
        if download_image_with_browser_simulation(url, task_url, save_path):
            return True
        print("浏览器模拟下载失败，尝试其他方式...")
    
    # 方式3: 使用requests库下载
    if download_image_with_requests(url, save_path):
        return True
        
    print("尝试最后一种下载方式...")
    
    # 方式4: 使用urllib库下载
    if download_image_with_urllib(url, save_path):
        return True
        
    # 所有方式都失败
    print(f"所有下载方式均失败: {url}")
    return False

def download_worker(task):
    """线程工作函数，处理单个下载任务"""
    image_url, image_path, task_url, task_id = task
    success = download_image(image_url, image_path, task_url)
    return {
        "task_id": task_id,
        "image_url": image_url,
        "image_path": image_path,
        "success": success
    }

def process_csv_file(csv_path, output_dir, num_threads=4):
    """处理单个CSV文件，提取Prompt文本保存为txt文件，并行下载图片链接指向的图片"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            # 显式指定引号处理选项，确保正确处理带引号的字段
            reader = csv.DictReader(
                csvfile, 
                quotechar='"',  # 使用双引号作为引用字符
                quoting=csv.QUOTE_ALL,  # 所有字段都被视为引用
                skipinitialspace=True  # 跳过引号后的初始空格
            )
            
            # 调试信息：打印CSV的字段名
            if reader.fieldnames:
                print("CSV文件字段名:")
                for i, field in enumerate(reader.fieldnames):
                    print(f"  {i+1}. {field}")
            else:
                print("警告: 无法读取CSV文件的字段名")
                return
                
            # 检查必要的字段是否存在
            # 定义所需字段，包括两种可能的任务ID字段名（大小写不同）
            required_prompt_and_image = ['Prompt', '图片链接']
            task_id_fields = ['任务id', '任务ID']
            
            # 检查Prompt字段（可能带有BOM字符）
            prompt_field = None
            for field in reader.fieldnames:
                if field == 'Prompt' or field.replace('\ufeff', '') == 'Prompt':
                    prompt_field = field
                    break
            
            missing_fields = []
            if not prompt_field:
                missing_fields.append('Prompt')
                
            # 检查图片链接字段
            if '图片链接' not in reader.fieldnames:
                missing_fields.append('图片链接')
                
            if missing_fields:
                print(f"错误: CSV文件 {csv_path} 缺少必要字段: {', '.join(missing_fields)}")
                return
            
            # 检查任务ID字段（支持大小写两种版本）
            task_id_field = None
            for field in task_id_fields:
                if field in reader.fieldnames:
                    task_id_field = field
                    break
            if not task_id_field:
                print(f"错误: CSV文件 {csv_path} 缺少必要字段 任务id/任务ID")
                return
            
            # 检查任务链接字段（可选）
            task_url_field = None
            task_url_possible_fields = ['任务链接', '任务URL', '链接', 'URL']
            for field in task_url_possible_fields:
                if field in reader.fieldnames:
                    task_url_field = field
                    print(f"找到任务链接字段: {field}")
                    break
            
            if task_url_field:
                print("该CSV包含任务链接字段，将用于增强图片下载功能")
            else:
                print("未找到任务链接字段，将使用普通方式下载图片")
            
            # 收集所有行数据
            rows = list(reader)
            row_count = len(rows)
            print(f"CSV文件共有 {row_count} 行数据")
            
            # 首先处理所有Prompt文本，并收集下载任务
            download_tasks = []
            txt_success_count = 0
            txt_error_count = 0
            
            print("正在处理Prompt文本...")
            for i, row in enumerate(rows):
                try:
                    # 获取任务ID
                    task_id = row.get(task_id_field, '').strip()
                    if not task_id:
                        print(f"警告: 第 {i+1} 行缺少任务ID，跳过")
                        txt_error_count += 1
                        continue
                    
                    # 清理任务ID，移除非法文件名字符
                    task_id = ''.join(c for c in task_id if c.isalnum() or c in '._- ')
                    if not task_id:
                        task_id = f"task_{i+1}"
                        print(f"警告: 任务ID只包含非法字符，使用替代ID: {task_id}")
                    
                    # 获取Prompt文本
                    prompt_text = row.get(prompt_field, '').strip()
                    
                    # 保存Prompt文本到txt文件
                    txt_path = os.path.join(output_dir, f"{task_id}.txt")
                    try:
                        with open(txt_path, 'w', encoding='utf-8') as txt_file:
                            txt_file.write(prompt_text)
                        txt_success_count += 1
                    except Exception as e:
                        print(f"保存Prompt文本失败 ({task_id}): {str(e)}")
                        txt_error_count += 1
                    
                    # 获取图片链接
                    image_url = row.get('图片链接', '').strip()
                    if not image_url:
                        print(f"警告: 第 {i+1} 行缺少图片链接，跳过图片下载")
                        continue
                        
                    # 获取任务链接（如果有）
                    task_url = None
                    if task_url_field:
                        task_url = row.get(task_url_field, '').strip()
                        
                    # 图片保存路径
                    image_path = os.path.join(output_dir, f"{task_id}.png")
                    
                    # 将任务添加到下载队列
                    download_tasks.append((image_url, image_path, task_url, task_id))
                    
                except Exception as e:
                    print(f"处理第 {i+1} 行时出错: {str(e)}")
                    txt_error_count += 1
            
            # 统计处理结果
            # 统计处理结果
            print(f"\nPrompt文本处理完成:")
            print(f"- 成功: {txt_success_count} 个")
            print(f"- 失败: {txt_error_count} 个")
            
            # 开始并行下载图片
            download_count = len(download_tasks)
            if download_count > 0:
                print(f"\n开始并行下载 {download_count} 张图片，使用 {num_threads} 个线程...")
                
                # 使用线程池执行下载任务
                successful_downloads = 0
                failed_downloads = 0
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                    # 创建一个进度条来显示下载进度
                    with tqdm(total=download_count, desc="下载进度", unit="张") as progress_bar:
                        # 并行提交所有下载任务
                        future_to_task = {executor.submit(download_worker, task): i for i, task in enumerate(download_tasks)}
                        
                        # 处理完成的任务
                        for future in concurrent.futures.as_completed(future_to_task):
                            task_index = future_to_task[future]
                            try:
                                result = future.result()
                                if result["success"]:
                                    successful_downloads += 1
                                else:
                                    failed_downloads += 1
                            except Exception as exc:
                                task_id = download_tasks[task_index][3]
                                print(f"任务 {task_id} 执行异常: {exc}")
                                failed_downloads += 1
                            finally:
                                # 更新进度条
                                progress_bar.update(1)
                
                # 显示下载统计结果
                print(f"\n图片下载完成:")
                print(f"- 成功: {successful_downloads} 张")
                print(f"- 失败: {failed_downloads} 张")
                print(f"- 总计: {download_count} 张")
                print(f"- 总计: {download_count} 张")
            else:
                print("\n没有找到需要下载的图片链接")
    except Exception as e:
        print(f"处理CSV文件时出错: {str(e)}")
        traceback.print_exc()

def process_directory(input_dir, output_dir, num_threads=4):
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.csv'):
            csv_path = os.path.join(input_dir, filename)
            print(f"\n正在处理: {csv_path}")
            process_csv_file(csv_path, output_dir, num_threads)

def main_interactive():
    """交互式模式的主函数"""
    # 显示命令行参数的使用方法
    print("=" * 80)
    print("MJ CSV下载工具 - 命令行参数使用方法")
    print("=" * 80)
    
    # 创建临时ArgumentParser对象以获取帮助信息
    temp_parser = argparse.ArgumentParser(description="MJ CSV下载工具 - 处理CSV数据并下载图片")
    temp_parser.add_argument('input_path', nargs='?', help='CSV文件或目录路径')
    temp_parser.add_argument('output_dir', nargs='?', help='文件保存目录')
    temp_parser.add_argument('--test-url', help='测试下载单个图片URL')
    temp_parser.add_argument('--test-task-url', help='测试下载时使用的任务URL（用于浏览器模拟下载）')
    temp_parser.add_argument('--test-output', help='测试下载图片的保存目录')
    temp_parser.add_argument('--check-curl', action='store_true', help='检查curl是否已安装')
    temp_parser.add_argument('--threads', '-t', type=int, default=4, help='并行下载的线程数 (默认: 4)')
    temp_parser.add_argument('--interactive', action='store_true', help='使用交互式模式运行脚本')
    
    # 获取格式化的帮助信息并打印
    formatter = temp_parser._get_formatter()
    temp_parser._print_message(temp_parser.format_help(), sys.stdout)
    
    print("\n当前正在使用交互式模式运行脚本。\n")
    print("=" * 80)
    print()
    
    # 获取输入路径
    while True:
        input_path = input("请输入CSV文件路径或目录路径: ").strip()
        if os.path.exists(input_path):
            break
        print("路径不存在，请重新输入！")
    
    # 获取输出目录
    while True:
        output_dir = input("请输入文件保存目录: ").strip()
        try:
            os.makedirs(output_dir, exist_ok=True)
            break
        except Exception as e:
            print(f"无法创建目录: {str(e)}，请重新输入！")
    
    process_input(input_path, output_dir, 4)  # 默认使用4个线程

def process_input(input_path, output_dir, num_threads=4):
    """处理输入路径和输出目录"""
    # 判断是单个文件还是目录并处理
    if os.path.isfile(input_path) and input_path.lower().endswith('.csv'):
        print(f"\n处理单个文件: {input_path}")
        process_csv_file(input_path, output_dir, num_threads)
    elif os.path.isdir(input_path):
        print(f"\n处理目录: {input_path}")
        process_directory(input_path, output_dir, num_threads)
    else:
        print("错误: 输入路径不是CSV文件也不是目录！")
    
    print("\n处理完成！")

def test_download_image(url, output_dir=None, task_url=None):
    """测试下载单个图片URL的功能
    
    参数:
    url -- 图片URL
    output_dir -- 输出目录，默认为当前目录下的test_images
    task_url -- 可选的任务URL，用于浏览器模拟下载
    """
    if not output_dir:
        output_dir = os.path.join(os.getcwd(), "test_images")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 从URL中获取文件名，如果无法获取则使用timestamp
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    if not file_name or file_name == "":
        file_name = f"test_image_{int(time.time())}.png"
    
    # 确保文件有扩展名
    if not os.path.splitext(file_name)[1]:
        file_name += ".png"
    
    save_path = os.path.join(output_dir, file_name)
    print(f"测试下载图片: {url}")
    if task_url:
        print(f"使用任务URL: {task_url}")
    print(f"保存路径: {save_path}")
    
    result = download_image(url, save_path, task_url)
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
        print("❌ curl未安装。作为可选的下载方式，推荐安装curl以提高下载成功率。")
        if platform.system() == "Windows":
            print("  Windows安装方法: 可以通过Scoop或Chocolatey安装，如:")
            print("  - 使用Chocolatey: choco install curl")
            print("  - 使用Scoop: scoop install curl")
            print("  或者从官方网站下载安装包: https://curl.se/windows/")
        elif platform.system() == "Darwin":  # macOS
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
    args = parser.parse_args()
    
    # 检查curl安装
    if args.check_curl:
        check_curl_installation()
        return
    
    # 测试模式：下载单个URL
    if args.test_url:
        test_download_image(args.test_url, args.test_output, args.test_task_url)
    # 交互式模式
    elif args.interactive:
        main_interactive()
    # 如果提供了命令行参数，使用命令行模式
    elif args.input_path and args.output_dir:
        input_path = args.input_path.strip()
        output_dir = args.output_dir.strip()
        
        # 验证输入路径存在
        if not os.path.exists(input_path):
            print(f"错误: 输入路径 '{input_path}' 不存在！")
            return
        
        # 尝试创建输出目录
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"错误: 无法创建输出目录 '{output_dir}': {str(e)}")
            return
        
        # 处理输入和输出
        process_input(input_path, output_dir, args.threads)
    else:
        # 如果没有提供足够的命令行参数，默认进入交互模式
        print("没有提供足够的命令行参数，默认进入交互模式...\n")
        main_interactive()

if __name__ == "__main__":
    main()
