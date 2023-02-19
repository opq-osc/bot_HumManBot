"""HumManBot系统"""
import json
import jieba
from re import sub

from botoy import jconfig, Action, logger
from botoy.contrib import plugin_receiver
from botoy.decorators import ignore_botself

from .core.chatbot import ChatBot
from .core.tool.filter import BSFilter

GROUP_BLACKLIST = ["139988954"]
SENSITIVE_WORDS_FILE = 'botoy/plugins/bot_HumManBot/core/resources/sensitive.txt'
BOT_NAME = '猪猪侠'
WEBQA_FLAG = '((WebQA))'
IMG_FLAG = '((img))'
BASE64_FLAG = '((base64))'
URL_FLAG = '((url))'
UNKNOWN_ANSWER = '无答案'

bot = ChatBot()

# 读取敏感词列表
gfw = BSFilter()
gfw.parse(SENSITIVE_WORDS_FILE)
action = Action(jconfig.qq)


@plugin_receiver.group
@ignore_botself
def receiver(ctx):
    msg_type = ctx.MsgType
    chat_type = "GroupMsg" if hasattr(ctx, 'FromGroupId') else "FriendMsg"

    if msg_type not in ["TextMsg", "AtMsg"]:
        return

    content = ctx.Content
    if msg_type == "AtMsg":
        try:
            content_data = json.loads(content)
            qq_uid = content_data['UserID'][0]
        except Exception as e:
            logger.warning(f"AtMsg消息编码失败\r\n {e}")
            return
        if qq_uid != jconfig.qq:
            return
        content = sub(r'@(.+) ', "", content_data['Content'])

    if chat_type == "GroupMsg":
        q_uin = getattr(ctx, 'FromGroupId', None)
        uin = getattr(ctx, 'FromUserId', None)

        if q_uin in GROUP_BLACKLIST:
            return

        message_list = list(jieba.cut(content))
        message_new = ''.join(
            gfw.filter(word, "*") if gfw.filter(word, "*").count("*") == len(word) else word for word in message_list)
        if '*' in message_new:
            logger.warning(message_new)
            return

        response = bot.response(content)
        if response is None:
            return
        elif response:
            response_text = "".join(
                response.replace(" ", "").replace("\r", "").replace("菲菲", BOT_NAME))
            if response_text != UNKNOWN_ANSWER and len(response_text) != 0:
                if WEBQA_FLAG in response_text:
                    if IMG_FLAG in response_text:
                        if BASE64_FLAG in response_text:
                            action.sendGroupPic(group=q_uin,
                                                picBase64Buf=response_text.replace("((WebQA))", "").replace("((img))",
                                                                                                            "").replace(
                                                    "((base64))", ""))
                            return
                        elif URL_FLAG in response_text:
                            action.sendGroupPic(group=q_uin,
                                                picUrl=response_text.replace("((WebQA))", "").replace("((img))",
                                                                                                      "").replace(
                                                    "((url))", ""))
                            return
                        else:
                            action.replyGroupMsg(group=q_uin, content=response_text.replace("((WebQA))", ""),
                                                 msgSeq=ctx.MsgSeq, user=ctx.FromUserId, msgTime=ctx.MsgTime,
                                                 rawContent=content)
                            return
                    else:
                        action.replyGroupMsg(group=q_uin, content=response_text.replace("((WebQA))", ""),
                                             msgSeq=ctx.MsgSeq, user=ctx.FromUserId, msgTime=ctx.MsgTime,
                                             rawContent=content)
                        return
                else:
                    action.replyGroupMsg(group=q_uin, content=response_text.replace("((WebQA))", ""), msgSeq=ctx.MsgSeq,
                                         user=ctx.FromUserId, msgTime=ctx.MsgTime, rawContent=content)
                    return
