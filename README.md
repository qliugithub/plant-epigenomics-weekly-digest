# Plant Epigenomics Weekly Digest

植物表观基因组、果实发育与多组学整合文献周报。已导入 2026-08-14、08-21、08-28、09-04 四期，共 13 篇文献。

支持按期浏览、关键词搜索、阅读优先级筛选，以及研究新意、关联、阅读重点和原文链接。

## 启用网站与每周更新

仓库代码与工作流已经准备好。是否能运行仍取决于下列仓库设置；代码上传不等于自动任务已成功运行。

1. 打开 [Pages 设置](https://github.com/qliugithub/plant-epigenomics-weekly-digest/settings/pages)，把 Source 设为 **GitHub Actions**。
2. 打开 [Publish existing archive](https://github.com/qliugithub/plant-epigenomics-weekly-digest/actions/workflows/publish.yml)，点击 **Run workflow**。这一步不需要 API 密钥，只发布已有周报。网站 URL 以成功的部署结果为准。
3. 在 [Actions Secrets](https://github.com/qliugithub/plant-epigenomics-weekly-digest/settings/secrets/actions) 添加名为 `OPENAI_API_KEY` 的 Repository secret。密钥只填写在 GitHub，不能提交进代码。OpenAI API 费用与 ChatGPT 订阅分开计费。
4. 可选：在 Actions Variables 设置 `OPENAI_MODEL`；默认 `gpt-4.1-mini`。
5. 打开 [Weekly literature digest](https://github.com/qliugithub/plant-epigenomics-weekly-digest/actions/workflows/weekly.yml)，点击 **Run workflow** 验证检索、分析、归档和发布。当天周报已经存在时脚本保留原内容，跳过生成，因而这种运行不能验证模型密钥。
6. 流程安排为每周五 **01:00 UTC / 09:00 Asia/Singapore**。GitHub 定时任务可能延迟；请检查 Actions 的运行记录和失败通知。公开仓库长期无活动时定时工作流可能暂停。

## 自动流程

- Europe PMC 检索最近 21 天的记录，分页获取并按标题 / DOI 去重，以覆盖收录延迟。
- 对相关候选摘要排序，最多将 35 篇交给 OpenAI Responses API，筛选 0–5 篇值得关注的文献。
- 返回的论文必须来自候选记录；标题、日期、来源和链接由原始检索记录填入。
- 以中文说明研究新意、与辣椒表观组研究的关系、阅读重点和局限。
- 成功后追加到 `dist/digest.json` 并提交至仓库，再发布 GitHub Pages。
- 检索或分析失败会中止，不覆盖旧归档；每个新加坡日期仅归档一期。
- 既有 ChatGPT 自动任务不受本仓库控制，也不会自动写入 ChatGPT Project。

## 内容边界

历史四期来自用户提供的原周报；此次建站没有重新核验全部论文及全文。自动生成的分析仅依据摘要，不声称阅读了全文、图表或补充材料。Europe PMC 有索引延迟与覆盖限制，不能代表全网文献或平台外的实质分析。请保留科研判断。

## Sites 与 GitHub Pages

已有 Sites 地址为私有静态快照：
https://plant-epigenomics-weekly.lq761244895.chatgpt.site

本仓库的工作流更新 **GitHub Pages**，不会同步刷新上述 Sites URL。GitHub Pages 是否已上线，以 Actions 成功结果为准。

## 本地验证

```sh
node --check dist/app.js
python -m py_compile scripts/update_digest.py
```

用任意 HTTP 静态服务器服务 `dist` 目录即可预览。

## 官方参考

- [Europe PMC API](https://europepmc.org/RestfulWebService)
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create/)
- [GitHub Pages 发布设置](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
