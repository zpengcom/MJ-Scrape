
 
 
 项目包含chrome插件和py下载脚本
 chrome插件使用：克隆项目 使用chrome加载目录 

 本项目由AI编写，本人只提需求+测试反馈
 
 
 MJ-CSV-下载脚本.py : 配合csv脚本下载工具
 ========================================================================
 脚本用途:
   该脚本用于处理包含Midjourney任务数据的CSV文件，提取并保存文本提示(Prompt)为txt文件，
   同时下载相应的图片。支持单个CSV文件处理和批量目录处理。

 主要功能:
   1. 从CSV提取Prompt文本并保存为txt文件，文件命名统一采用扩展模式的命名方式（例如 任务ID_0.txt）
   2. 下载CSV中的图片链接指向的图片，图片文件名与文本文件对应（例如 任务ID_0.png）
   3. 支持单个CSV文件或整个目录的批量处理
   4. 支持多线程并行下载，提高处理速度
   5. 提供四种下载方式供用户选择（默认使用curl方式），用户可通过参数或交互提示选择方式
   6. 【扩展模式】：在扩展模式下，每个任务构造0_0至0_3四个下载任务（命名如 taskID_0、taskID_1...），
      如果某个图片下载失败，则对应的txt文件不生成；扩展模式下最多重试1次，普通模式下重试2次。
   7. 【优化】：如果保存的目录中已存在要下载的图片和文本文件，则自动略过不处理。

 命令行参数说明:
   python MJ-CSV-DL.py [input_path] [output_dir] [选项]
   python MJ-CSV-DL.py  # 不带参数时默认进入交互模式

   位置参数:
     input_path            CSV文件或包含CSV文件的目录路径
     output_dir            文件(文本和图片)保存目录

   可选参数:
     -h, --help            显示帮助信息并退出
     --test-url URL        测试下载单个图片URL
     --test-task-url URL   测试下载时使用的任务URL（用于浏览器模拟下载）
     --test-output DIR     测试下载图片的保存目录
     --check-curl          检查curl是否已安装
     --threads N, -t N     并行下载的线程数 (默认: 4)
     --extended            启用扩展模式下载多个图片（构造0_0至0_3）
     --method METHOD       选择下载方式，可选值：curl, browser, requests, urllib (默认: curl)

 使用示例:
   1. 处理单个CSV文件（普通模式，生成 taskID_0.xxx）:
      python MJ-CSV-DL.py path/to/file.csv path/to/output --method curl

   2. 批量处理目录中的所有CSV文件（扩展模式，生成 taskID_0 ～ taskID_3）:
      python MJ-CSV-DL.py path/to/directory path/to/output --extended --method curl

   3. 使用8个线程进行并行下载:
      python MJ-CSV-DL.py path/to/file.csv path/to/output --threads 8 --method curl

   4. 测试下载单个图片:
      python MJ-CSV-DL.py --test-url https://cdn.midjourney.com/xxx/0_0.png --method curl

   5. 检查curl是否已安装:
      python MJ-CSV-DL.py --check-curl

 CSV文件格式要求:
   CSV文件必须包含以下字段:
   - 'Prompt': 文本提示内容
   - '任务id'或'任务ID': 用于文件命名的任务标识符
   - '图片链接': 要下载的图片URL

   可选字段:
   - '任务链接': 任务页面URL，用于增强图片下载功能

 注意事项:
   1. 扩展模式下针对下载失败的图片最多重试1次，且下载失败时不生成对应的txt文件
   2. 普通模式下下载失败最多重试2次
   3. 大量图片下载时建议使用多线程(--threads参数)提高效率
   4. 字段名区分大小写，但'任务id'和'任务ID'都被支持
   5. 如果保存的目录中已存在要下载的图片和文本文件，则自动略过不处理
