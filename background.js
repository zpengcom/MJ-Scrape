// 监听工具栏图标点击事件
chrome.action.onClicked.addListener(() => {
  // 打开 MidJourney 网页
  chrome.tabs.create({ url: "https://www.midjourney.com/" });
});