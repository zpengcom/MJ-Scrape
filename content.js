// 避免重复创建元素的工具函数
function ensureElementDoesNotExist(id) {
    const existingElement = document.getElementById(id);
    if (existingElement) {
        existingElement.remove();
    }
}

// 创建设置面板
function createSettingsPanel() {
    const panel = document.createElement('div');
    panel.id = 'settingsPanel';
    panel.className = 'settings-panel';
    panel.style.display = 'none';
    
    panel.innerHTML = `
        <div class="settings-header">
            <h3>抓取设置</h3>
            <button class="close-button">×</button>
        </div>
        <div class="setting-item">
            <label for="scrollDelay">滚动延迟(毫秒) 使用上下键可调整:</label>
            <input type="number" id="scrollDelay" min="100" max="5000" step="100" value="${localStorage.getItem('scrollDelay') || 1000}">
        </div>
        <div class="settings-footer">
            <button id="saveSettings" class="save-button">
                保存设置
            </button>
        </div>
    `;
    
    document.body.appendChild(panel);
    
    document.getElementById('saveSettings').addEventListener('click', () => {
        const delay = document.getElementById('scrollDelay').value;
        localStorage.setItem('scrollDelay', delay);
        panel.style.display = 'none';
    });

    panel.querySelector('.close-button').addEventListener('click', () => {
        panel.style.display = 'none';
    });
}

// 创建结果窗口
function createResultWindow() {
    if (document.getElementById('scrapeResult')) return;

    const resultDiv = document.createElement('div');
    resultDiv.id = 'scrapeResult';
    resultDiv.classList.add('dark-mode', 'result-window');
    resultDiv.style.display = 'none';
    
    const headerBar = document.createElement('div');
    headerBar.className = 'window-header';
    headerBar.innerHTML = `
        <div class="header-content">
            <div class="title-section">
                <div class="drag-handle">结果窗口</div>
                <div class="status-text">等待抓取...</div>
            </div>
            <div class="header-controls">
                <button id="select-all" class="small-button">全选</button>
                <button id="invert-selection" class="small-button">反选</button>
                <button class="export-button" style="display: none;">导出CSV</button>
                <button class="window-close" title="关闭">×</button>
            </div>
        </div>
    `;
    resultDiv.appendChild(headerBar);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'result-content';
    resultDiv.appendChild(contentDiv);

    const bottomIndicator = document.createElement('div');
    bottomIndicator.className = 'bottom-indicator';
    bottomIndicator.textContent = '到底了';
    bottomIndicator.style.display = 'none';
    contentDiv.appendChild(bottomIndicator);

    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'resize-handle';
    resultDiv.appendChild(resizeHandle);

    document.body.appendChild(resultDiv);

    const selectAllButton = headerBar.querySelector('#select-all');
    const invertSelectionButton = headerBar.querySelector('#invert-selection');

    selectAllButton.addEventListener('click', () => {
        const checkboxes = contentDiv.querySelectorAll('.select-item');
        checkboxes.forEach(checkbox => checkbox.checked = true);
    });

    invertSelectionButton.addEventListener('click', () => {
        const checkboxes = contentDiv.querySelectorAll('.select-item');
        checkboxes.forEach(checkbox => checkbox.checked = !checkbox.checked);
    });

    let isDragging = false;
    let isResizing = false;
    let currentX, currentY, initialX, initialY;
    let startWidth, startHeight, startMouseX, startMouseY;

    headerBar.addEventListener('mousedown', (e) => {
        if (e.target.classList.contains('window-close') || e.target.classList.contains('export-button')) return;
        isDragging = true;
        initialX = e.clientX - resultDiv.offsetLeft;
        initialY = e.clientY - resultDiv.offsetTop;
    });

    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            resultDiv.style.left = `${currentX}px`;
            resultDiv.style.top = `${currentY}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    headerBar.querySelector('.window-close').addEventListener('click', () => {
        resultDiv.style.display = 'none';
        const scrapeButton = document.getElementById('scrapeButton');
        if (scrapeButton) {
            scrapeButton.querySelector('.icon-stop').style.display = 'none';
            scrapeButton.querySelector('.icon-search').style.display = 'block';
            scrapeButton.title = '开始抓取';
        }
    });

    resultDiv.style.top = '50%';
    resultDiv.style.left = '50%';
    resultDiv.style.transform = 'translate(-50%, -50%)';
    resultDiv.style.width = '600px';
    resultDiv.style.height = '400px';

    function constrainToViewport() {
        const rect = resultDiv.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const viewportWidth = window.innerWidth;

        if (rect.top < 0) {
            resultDiv.style.top = '20px';
            resultDiv.style.transform = 'translateX(-50%)';
        }
        if (rect.bottom > viewportHeight) {
            resultDiv.style.top = (viewportHeight - rect.height - 20) + 'px';
            resultDiv.style.transform = 'translateX(-50%)';
        }
        if (rect.left < 0) {
            resultDiv.style.left = '20px';
            resultDiv.style.transform = 'none';
        }
        if (rect.right > viewportWidth) {
            resultDiv.style.left = (viewportWidth - rect.width - 20) + 'px';
            resultDiv.style.transform = 'none';
        }
    }

    document.addEventListener('mousemove', () => {
        if (isDragging) {
            constrainToViewport();
        }
    });

    const resizeObserver = new ResizeObserver(() => {
        constrainToViewport();
    });
    resizeObserver.observe(resultDiv);

    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        e.preventDefault();
        startWidth = resultDiv.offsetWidth;
        startHeight = resultDiv.offsetHeight;
        startMouseX = e.clientX;
        startMouseY = e.clientY;
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        const deltaX = e.clientX - startMouseX;
        const deltaY = e.clientY - startMouseY;

        const newWidth = Math.max(400, Math.min(window.innerWidth - 40, startWidth + deltaX));
        const newHeight = Math.max(300, Math.min(window.innerHeight - 40, startHeight + deltaY));

        resultDiv.style.width = `${newWidth}px`;
        resultDiv.style.height = `${newHeight}px`;

        constrainToViewport();
    });

    document.addEventListener('mouseup', () => {
        isResizing = false;
    });

    contentDiv.addEventListener('scroll', () => {
        const scrollTop = contentDiv.scrollTop;
        const scrollHeight = contentDiv.scrollHeight;
        const clientHeight = contentDiv.clientHeight;

        if (scrollTop + clientHeight >= scrollHeight - 2) {
            bottomIndicator.style.display = 'block';
        } else {
            bottomIndicator.style.display = 'none';
        }
    });
}

// 创建切换显示/隐藏按钮
function createToggleButton(buttonContainer) {
    ensureElementDoesNotExist('toggleButton');

    const toggleButton = document.createElement('button');
    toggleButton.id = 'toggleButton';
    toggleButton.className = 'control-button icon-button';
    toggleButton.title = '显示/隐藏结果';
    toggleButton.innerHTML = `
        <svg class="icon-eye-open" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
        </svg>
        <svg class="icon-eye-closed" viewBox="0 0 24 24" width="20" height="20" style="display: none;">
            <path fill="currentColor" d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
        </svg>
    `;
    
    buttonContainer.appendChild(toggleButton);

    toggleButton.addEventListener('click', () => {
        const resultDiv = document.getElementById('scrapeResult');
        const eyeOpen = toggleButton.querySelector('.icon-eye-open');
        const eyeClosed = toggleButton.querySelector('.icon-eye-closed');
        
        if (resultDiv) {
            if (resultDiv.style.display === 'none') {
                resultDiv.style.display = 'block';
                eyeOpen.style.display = 'none';
                eyeClosed.style.display = 'block';
            } else {
                resultDiv.style.display = 'none';
                eyeOpen.style.display = 'block';
                eyeClosed.style.display = 'none';
            }
        }
    });
}

// 创建设置按钮
function createSettingsButton(buttonContainer) {
    ensureElementDoesNotExist('settingsButton');

    const settingsButton = document.createElement('button');
    settingsButton.id = 'settingsButton';
    settingsButton.className = 'control-button icon-button';
    settingsButton.title = '设置';
    settingsButton.innerHTML = `
        <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
        </svg>
    `;
    
    buttonContainer.appendChild(settingsButton);

    settingsButton.addEventListener('click', () => {
        const panel = document.getElementById('settingsPanel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    });
}

// 创建抓取按钮
function createScrapeButton(buttonContainer) {
    ensureElementDoesNotExist('scrapeButton');

    const scrapeButton = document.createElement('button');
    scrapeButton.id = 'scrapeButton';
    scrapeButton.className = 'control-button icon-button';
    scrapeButton.title = '开始抓取';
    scrapeButton.innerHTML = `
        <svg class="icon-search" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <svg class="icon-stop" viewBox="0 0 24 24" width="20" height="20" style="display: none;">
            <path fill="currentColor" d="M18,18H6V6H18V18Z" />
        </svg>
    `;
    
    buttonContainer.appendChild(scrapeButton);
    
    let isScraping = false;
    
    scrapeButton.addEventListener('click', () => {
        const resultDiv = document.getElementById('scrapeResult');
        if (!resultDiv) return;
        
        isScraping = !isScraping;
        
        resultDiv.style.display = 'block';
        
        if (isScraping) {
            scrapeButton.querySelector('.icon-search').style.display = 'none';
            scrapeButton.querySelector('.icon-stop').style.display = 'block';
            scrapeButton.title = '停止抓取';
            scrapeButton.classList.add('scraping');
            resultDiv.querySelector('.status-text').textContent = '正在抓取...';
            scrollAndScrape(() => isScraping);
        } else {
            scrapeButton.querySelector('.icon-search').style.display = 'block';
            scrapeButton.querySelector('.icon-stop').style.display = 'none';
            scrapeButton.title = '开始抓取';
            scrapeButton.classList.remove('scraping');
            resultDiv.querySelector('.status-text').textContent = '抓取完成';
        }
    });
}

// 检查内容是否加载完成
function isContentLoaded(pageScroll) {
    const loadingIndicators = pageScroll.querySelectorAll('[class*="loading"], [class*="spinner"]');
    return loadingIndicators.length === 0;
}

// 滚动并抓取数据
async function scrollAndScrape(checkActive) {
    await new Promise(resolve => setTimeout(resolve, 50));
    
    const scrollDelay = parseInt(localStorage.getItem('scrollDelay') || 100);
    
    const resultDiv = document.getElementById('scrapeResult');
    if (!resultDiv) return;
    
    const contentDiv = resultDiv.querySelector('.result-content');
    
    const scrapedData = [];
    const seenIds = new Set();
    
    let lastHeight = 0;
    let sameHeightCount = 0;
    const maxSameHeight = 5;
    
    console.log('开始抓取...');
    
    try {
        await navigator.clipboard.readText();
    } catch (error) {
        alert('需要剪贴板访问权限才能获取完整的prompt信息');
        return;
    }
    
    while (checkActive()) {
        const pageScroll = document.querySelector('#pageScroll') || document.querySelector('.infinite-scroll-component');
        if (!pageScroll) {
            console.error('未找到滚动容器');
            break;
        }
        
        const visibleLinks = Array.from(pageScroll.querySelectorAll('a[href*="/jobs/"], a[href*="/imagine"]'));
        console.log(`找到 ${visibleLinks.length} 个图片链接`);
        
        for (const link of visibleLinks) {
            if (!checkActive()) {
                console.log('处理图片过程中收到停止指令，退出内层循环');
                break;
            }
            
            try {
                let jobId;
                if (link.href.includes('/jobs/')) {
                    jobId = link.href.split('/jobs/')[1]?.split('?')[0];
                } else if (link.href.includes('/imagine')) {
                    jobId = link.href.split('/imagine/')[1]?.split('/')[0];
                }
                
                if (!jobId || seenIds.has(jobId)) {
                    console.log(`跳过已处理的 jobId: ${jobId}`);
                    continue;
                }
                
                const parentContainer = link.closest('div[class*="grid-item"], div[class*="aspect-square"]') || link.parentElement;
                const style = link.getAttribute('style');
                let imgLink = getMaxSizeImageUrl(style);
                
                if (imgLink === '未找到图片') {
                    const imgElement = parentContainer.querySelector('img');
                    if (imgElement) {
                        imgLink = imgElement.src;
                    }
                }
                
                if (imgLink !== '未找到图片') {
                    const userInfoContainer = parentContainer.querySelector(
                        'div[class*="grow relative flex items-center min-h-[32px]"], div[class*="flex items-center"]'
                    );
                    
                    const userInfo = userInfoContainer ? extractUserInfo(userInfoContainer) : 
                        { userName: '未找到用户名', userId: '', userProfileLink: '' };
                    
                    let prompt = '未找到prompt';
                    const promptButtonContainer = parentContainer.querySelector(
                        'div[class*="flex shrink-0 items-center"][class*="-gap"][class*="justify-end"][class*="text-white"][class*="pointer-events-auto"]'
                    );
                    
                    if (promptButtonContainer) {
                        console.log('找到 Prompt 按钮容器:', promptButtonContainer);
                        
                        const copyButton = promptButtonContainer.querySelector(
                            'button[aria-label*="copy"], button[title*="copy"], button[aria-label*="prompt"], button[title*="prompt"], button[class*="copy"], button[data-testid*="copy"], button[aria-label*="Copy"], button[title*="Copy"]'
                        );
                        
                        if (copyButton) {
                            console.log('找到 Copy prompt 按钮:', copyButton);
                            try {
                                const originalClipboard = await navigator.clipboard.readText().catch(() => '');
                                const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
                                copyButton.dispatchEvent(clickEvent);
                                await new Promise(resolve => setTimeout(resolve, 200));
                                prompt = await navigator.clipboard.readText().catch(err => {
                                    console.error('读取剪切板失败:', err);
                                    return '未找到prompt';
                                });
                                if (originalClipboard !== prompt) {
                                    await navigator.clipboard.writeText(originalClipboard).catch(err => {
                                        console.error('恢复剪切板失败:', err);
                                    });
                                }
                            } catch (error) {
                                console.error('获取 Prompt 时出错:', error);
                                prompt = '获取prompt失败';
                            }
                        } else {
                            console.warn('未找到 Copy prompt 按钮');
                        }
                    } else {
                        console.warn('未找到 Prompt 按钮容器');
                    }
                    
                    if (!seenIds.has(jobId)) {
                        seenIds.add(jobId);
                        console.log(`添加新数据，jobId: ${jobId}`);
                        const { promptText, promptParams } = splitPrompt(prompt);
                        scrapedData.push({
                            imgLink,
                            jobLink: link.href,
                            jobId,
                            userName: userInfo.userName,
                            userId: userInfo.userId,
                            userProfileLink: userInfo.userProfileLink,
                            prompt: promptText,
                            promptParams,
                            metadata: ''
                        });
                        resultDiv.querySelector('.status-text').textContent = 
                            `正在抓取中...（已抓取 ${scrapedData.length} 张不重复图片）`;
                        updateResultDisplay(scrapedData, contentDiv, true);
                    }
                }
            } catch (error) {
                console.error('处理图片时出错:', error);
            }
        }
        
        if (!checkActive()) break;

        while (!isContentLoaded(pageScroll)) {
            if (!checkActive()) break;
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        if (!checkActive()) break;

        const currentHeight = pageScroll.scrollTop;
        pageScroll.scrollTo({
            top: currentHeight + 600,
            behavior: 'smooth'
        });
        
        await new Promise(resolve => setTimeout(resolve, scrollDelay));
        
        if (currentHeight === lastHeight) {
            sameHeightCount++;
            if (sameHeightCount >= maxSameHeight) {
                console.log('已到达页面底部，停止抓取');
                const scrapeButton = document.getElementById('scrapeButton');
                if (scrapeButton) {
                    scrapeButton.querySelector('.icon-search').style.display = 'block';
                    scrapeButton.querySelector('.icon-stop').style.display = 'none';
                    scrapeButton.title = '开始抓取';
                    scrapeButton.classList.remove('scraping');
                    resultDiv.querySelector('.status-text').textContent = 
                        `抓取完成（共抓取 ${scrapedData.length} 张不重复图片）`;
                }
                break;
            }
        } else {
            sameHeightCount = 0;
            lastHeight = currentHeight;
        }
    }
    
    const button = document.getElementById('scrapeButton');
    if (button) {
        button.title = '开始抓取';
        button.classList.remove('scraping');
        button.querySelector('.icon-search').style.display = 'block';
        button.querySelector('.icon-stop').style.display = 'none';
        resultDiv.querySelector('.status-text').textContent = 
            `抓取完成（共抓取 ${scrapedData.length} 张不重复图片）`;
    }
    
    console.log('抓取结束，最终数据量:', scrapedData.length);
    updateResultDisplay(scrapedData, contentDiv, false);
}



// 分离 Prompt 和 Prompt 参数
function splitPrompt(fullPrompt) {
    const paramStartIndex = fullPrompt.indexOf('--');
    if (paramStartIndex === -1) {
        return { promptText: fullPrompt.trim(), promptParams: '' };
    }
    return {
        promptText: fullPrompt.substring(0, paramStartIndex).trim(),
        promptParams: fullPrompt.substring(paramStartIndex).trim()
    };
}


// 获取最大尺寸图片链接并去掉分辨率标记
function getMaxSizeImageUrl(style) {
    if (!style) return '未找到图片';
    
    const urls = style.match(/url\("([^"]+)"\)/g) || [];
    const imageUrls = urls.map(url => url.match(/url\("([^"]+)"\)/)[1]);
    
    const maxUrl = imageUrls.reduce((max, current) => {
        const currentRes = current.match(/(\d+)_N\.(webp|png)$/);
        const maxRes = max.match(/(\d+)_N\.(webp|png)$/);
        
        if (!currentRes) return max;
        if (!maxRes) return current;
        
        return parseInt(currentRes[1]) > parseInt(maxRes[1]) ? current : max;
    }, imageUrls[0] || '未找到图片');
    
    if (maxUrl !== '未找到图片') {
        return maxUrl.replace(/_\d+_N(\.(webp|png))$/, '$1');
    }
    return maxUrl;
}

// 提取用户信息
function extractUserInfo(container) {
    const userInfo = {
        userName: '未找到用户名',
        userId: '',
        userProfileLink: ''
    };

    try {
        const userLink = container.querySelector('a[href*="user_id="]');
        if (userLink) {
            userInfo.userName = userLink.textContent.trim();
            const userIdMatch = userLink.href.match(/user_id=([^&]+)/);
            if (userIdMatch) {
                userInfo.userId = userIdMatch[1];
                userInfo.userProfileLink = userLink.href;
            }
        }
    } catch (error) {
        console.error('提取用户信息时出错:', error);
    }
    
    return userInfo;
}

// 更新结果显示
function updateResultDisplay(scrapedData, contentDiv, isPartial = false) {
    if (!isPartial) {
        contentDiv.innerHTML = '';
    }

    const newItems = isPartial ? [scrapedData[scrapedData.length - 1]] : scrapedData;
    
    newItems.forEach((newItem, index) => {
        // 预览图保持 _384_N.webp 不变
        let previewImgLink = newItem.imgLink.replace(/(\.(webp|png))$/, '_384_N$1');
        // 展示窗口中的图片链接强制替换为 .png
        let displayImgLink = newItem.imgLink.replace(/\.webp$/, '.png');
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'result-item';
        itemDiv.innerHTML = `
            <input type="checkbox" class="select-item" data-id="${newItem.jobId}" checked>
            <img src="${previewImgLink}" alt="Preview" style="width:100px; height:auto; border-radius:4px;" onerror="this.src='${newItem.imgLink}'">
            <div class="content">
                <p><strong>图片 ${index + 1}:</strong></p>
                <p>Prompt: <span class="prompt-text" style="cursor: pointer;" title="点击复制">${newItem.prompt}</span>
                    ${newItem.promptParams ? `<span class="prompt-params" style="color: #888;">${newItem.promptParams}</span>` : ''}
                </p>
                <p>图片链接: <a href="${displayImgLink}" target="_blank">${displayImgLink}</a></p>
                <p>任务ID: ${newItem.jobId}</p>
                <p>用户名: <a href="${newItem.userProfileLink}" target="_blank">${newItem.userName}</a></p>
                <p>用户ID: ${newItem.userId}</p>
            </div>
        `;
        contentDiv.appendChild(itemDiv);

        const promptTextElement = itemDiv.querySelector('.prompt-text');
        promptTextElement.addEventListener('click', () => {
            navigator.clipboard.writeText(newItem.prompt).then(() => {
                console.log(`已复制 Prompt 到剪切板: ${newItem.prompt}`);
                promptTextElement.style.color = '#4caf50';
                setTimeout(() => promptTextElement.style.color = '', 1000);
            }).catch(err => {
                console.error('复制失败:', err);
            });
        });
    });

    const exportButton = document.querySelector('.export-button');
    if (scrapedData.length > 0) {
        exportButton.style.display = 'inline-block';
        exportButton.onclick = () => exportToCSV(scrapedData);
    }
}

// 导出为 CSV
function exportToCSV(scrapedData) {
    const selectedIds = Array.from(document.querySelectorAll('.select-item:checked')).map(cb => cb.dataset.id);
    const selectedData = scrapedData.filter(item => selectedIds.includes(item.jobId));
    
    if (selectedData.length === 0) {
        alert('请先选择要导出的项');
        return;
    }
    
    const BOM = '\uFEFF';
    const csvContent = BOM + [
        ['Prompt', 'Prompt 参数', '任务ID', '任务链接', '图片链接', '用户名', '用户ID', '用户主页', '其他信息'].join(','),
        ...selectedData.map(item => {
            // 导出时强制将图片链接中的 .webp 替换为 .png
            let exportImgLink = item.imgLink.replace(/\.webp$/, '.png');
            return [
                `"${item.prompt.replace(/"/g, '""')}"`,
                `"${item.promptParams.replace(/"/g, '""')}"`,
                item.jobId,
                item.jobLink,
                exportImgLink,
                item.userName,
                item.userId,
                item.userProfileLink,
                `"${item.metadata.replace(/"/g, '""')}"`
            ].join(',');
        })
    ].join('\n');

    const now = new Date();
    const utc8Date = new Date(now.getTime() + (8 * 60 * 60 * 1000));
    const dateStr = utc8Date.toISOString().replace(/[:.]/g, '-').replace('T', '_').split('.')[0];

    let fileNamePrefix = 'MJ';
    const url = window.location.href;

    if (url.includes('tab=top')) {
        fileNamePrefix = 'MJ-top';
    } else if (url.includes('tab=likes')) {
        fileNamePrefix = 'MJ-likes';
    } else if (url.includes('user_id=')) {
        const userIdMatch = url.match(/user_id=([^&]+)/);
        const userId = userIdMatch ? userIdMatch[1] : 'unknown';
        const userName = selectedData.length > 0 && selectedData[0].userName !== '未找到用户名' 
            ? selectedData[0].userName.replace(/[^a-zA-Z0-9_-]/g, '_') : 'unknown';
        fileNamePrefix = `MJ-${userName}-${userId}`;
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${fileNamePrefix}_${dateStr}.csv`;
    link.click();
}

// 添加样式
const style = document.createElement('style');
style.textContent = `
    .button-container {
        display: flex;
        flex-direction: row;
        gap: 0;
    }
    
    .control-button {
        background-color: #222222;
        color: white;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        font-size: 14px;
        font-weight: 600;
        text-align: center;
        margin: 0;
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    .control-button:last-child {
        border-right: none;
    }
    
    .control-button.icon-button {
        width: 44px;
        height: 40px;
        padding: 8px;
    }
    
    .control-button svg {
        width: 20px;
        height: 20px;
        display: block;
        color: white;
    }
    
    .control-button:hover {
        background-color: #333333;
    }
    
    .control-button:active {
        background-color: #1a1a1a;
    }
    
    .control-button:disabled {
        background-color: #555555;
        cursor: not-allowed;
        opacity: 0.7;
    }
    
    .control-button.scraping {
        background-color: #d32f2f !important;
    }
    
    .control-button.scraping:hover {
        background-color: #e53935 !important;
    }
    
    .result-window {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        color: white;
        z-index: 10001;
        width: 600px;
        height: 400px;
        max-width: calc(100vw - 40px);
        max-height: calc(100vh - 40px);
        min-width: 400px;
        min-height: 300px;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        overflow: hidden;
    }
    
    .window-header {
        background-color: #222;
        padding: 10px 15px;
        flex-shrink: 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #333;
    }
    
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }
    
    .title-section {
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    
    .header-controls {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .drag-handle {
        font-weight: bold;
        font-size: 16px;
        cursor: move;
        user-select: none;
        color: #e0e0e0;
    }
    
    .status-text {
        color: #4caf50;
        font-size: 13px;
        font-weight: normal;
    }
    
    .export-button {
        background-color: #4caf50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        cursor: pointer;
        font-size: 13px;
        transition: all 0.2s ease;
    }
    
    .export-button:hover {
        background-color: #43a047;
    }
    
    .small-button {
        background-color: #4caf50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        cursor: pointer;
        font-size: 12px;
        margin-right: 5px;
        transition: all 0.2s ease;
    }
    
    .small-button:hover {
        background-color: #43a047;
    }
    
    .window-close {
        background: none;
        border: none;
        color: #e0e0e0;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        line-height: 1;
    }
    
    .window-close:hover {
        color: #ff5252;
    }
    
    .result-content {
        height: calc(100% - 60px);
        max-height: calc(100% - 60px);
        overflow-y: auto;
        overflow-x: hidden;
        padding: 15px;
        padding-bottom: 40px;
        background-color: #1a1a1a;
        box-sizing: border-box;
        position: relative;
    }
    
    .result-content:hover {
        scrollbar-color: #888 #333;
    }
    
    .result-content::-webkit-scrollbar {
        width: 10px;
    }
    
    .result-content::-webkit-scrollbar-track {
        background: #222;
        border-radius: 5px;
    }
    
    .result-content::-webkit-scrollbar-thumb {
        background: #666;
        border-radius: 5px;
    }
    
    .result-content::-webkit-scrollbar-thumb:hover {
        background: #888;
    }
    
    .result-item {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        padding: 15px;
        background-color: #2a2a2a;
        border-radius: 6px;
        margin-bottom: 15px;
        border: 1px solid #444;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        transition: all 0.2s ease;
    }
    
    .result-item:hover {
        background-color: #353535;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    }
    
    .result-item img {
        width: 100px;
        height: auto;
        border-radius: 4px;
    }
    
    .result-item .content {
        flex: 1;
    }
    
    .result-item p {
        margin: 6px 0;
        font-size: 14px;
        line-height: 1.6;
        color: #ffffff;
    }
    
    .result-item a {
        color: #66b0ff;
        text-decoration: none;
    }
    
    .result-item a:hover {
        color: #88ccff;
        text-decoration: underline;
    }
    
    .resize-handle {
        position: absolute;
        bottom: 0;
        right: 0;
        width: 15px;
        height: 15px;
        background-color: #555;
        cursor: nwse-resize;
    }
    
    .bottom-indicator {
        text-align: center;
        color: #888;
        font-size: 12px;
        padding: 10px 0;
        position: sticky;
        bottom: 0;
        background-color: #1a1a1a;
        border-top: 1px solid #333;
    }
    
    .settings-panel {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: #1a1a1a;
        color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        z-index: 10002;
        min-width: 300px;
    }
    
    .settings-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .settings-header h3 {
        margin: 0;
    }
    
    .close-button {
        background: none;
        border: none;
        color: #fff;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        line-height: 1;
    }
    
    .close-button:hover {
        color: #ff4444;
    }
    
    .setting-item {
        margin: 15px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .setting-item input {
        background-color: #333;
        color: white;
        border: 1px solid #444;
        padding: 5px;
        border-radius: 4px;
        width: 100px;
    }
    
    .setting-item label {
        min-width: 120px;
    }
    
    .settings-footer {
        margin-top: 20px;
        display: flex;
        justify-content: flex-end;
    }
    
    .save-button {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 8px 16px;
        background-color: #28a745;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .save-button:hover {
        background-color: #218838;
    }
`;
document.head.appendChild(style);

// 初始化函数
function init() {
    const url = window.location.href;
    const isExplorePage = url.includes('https://www.midjourney.com/explore') && 
                         (url.includes('tab=') || url.includes('user_id='));
    
    if (!isExplorePage) {
        console.log('MJ抓取工具: 当前页面不支持抓取，仅支持 https://www.midjourney.com/explore?tab= 或 ?user_id= 的页面');
        return;
    }

    console.log('MJ抓取工具: 初始化开始');
    
    createSettingsPanel();
    
    const buttonContainer = document.createElement('div');
    buttonContainer.id = 'buttonContainer';
    buttonContainer.className = 'button-container';
    buttonContainer.style.position = 'fixed';
    buttonContainer.style.bottom = '20px';
    buttonContainer.style.right = '20px';
    buttonContainer.style.zIndex = '10000';
    buttonContainer.style.display = 'flex';
    buttonContainer.style.boxShadow = '0 3px 8px rgba(0,0,0,0.4)';
    buttonContainer.style.borderRadius = '6px';
    buttonContainer.style.overflow = 'hidden';
    document.body.appendChild(buttonContainer);

    createScrapeButton(buttonContainer);
    createToggleButton(buttonContainer);
    createSettingsButton(buttonContainer);

    createResultWindow();
    
    console.log('MJ抓取工具: 所有UI组件已创建');
}

init();
