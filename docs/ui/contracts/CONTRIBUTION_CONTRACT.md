# Contribution Contract

> JSON：`docs/ui/contracts/json/contribution.json`。
> 完整 Transaction Flow，不是静态表单页。

## 1. 第一屏

```text
你刚刚知道了什么？
```

5 个消费者选项：
```text
我看到了新的规则
我在现场看到动物
工作人员进行了处理
我发现了相关设施
场所信息有误
```

## 2. 选中后

3–4 个 focused step（动态 per-choice）：entry → quick/signage/rule/reality form → done。

## 3. Final

```text
已提交待核验
```

绝不出现在提交成功时显示「规则已更新」。

## 4. Guards

- needs-place guard（`contribute-needs-place`）：未选场所时，隐藏 QueryContext，给出 去搜索场所 / 看地图 链接；
- signed-in guard：未登录 → 登录/注册链接。

## 5. 必须测试（Playwright）

- needs-place guard；
- real flow entry（选择选项后进入对应 step）；
- intermediate step（填写 → 下一步）；
- submit/done；
- mobile。

不能只凭 guard 页面存在就判 PASS。

## 6. 语言

- 全部消费者文案；无 `candidate` / `reality_report` / `pending_review` / actioned enum 原文。