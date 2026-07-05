import asyncio
import re
from telethon import TelegramClient, events, tl
from telethon.errors import FloodWaitError, PeerFloodError

# --- ဖြည့်စွက်ရန်နေရာ ---
API_ID = 31769145
API_HASH = "d283e534906cd08d3e329445ddd86f83"
# ------------------------

client = TelegramClient("user_bot_session", API_ID, API_HASH)

GLOBAL_DELAY = 5  # ပုံမှန် Delay က 5 စက္ကန့်
running_loops = {}  # { chat_id: { delay: 5, targets: { user_id: { task, msg_ids_pool: [], current_pool_idx: 0, msg_map: {}, active: True } } } }

# အဝိုင်းလည်နေစဉ် စာအသစ်ဝင်ပြီး Loop ပတ်တာကိုပဲ ခေတ္တရပ်မည့် Lock
IS_FLOODED = False
FLOOD_LOCK = asyncio.Lock()

# စစ်မြေပြင်သုံး စာသားများ
insult_messages = [
"ငါလိုးမသားနာနာကိုက်လေ",
"ခွေးဝဲစားစောက်အဆင့်နဲ့ငါလိုးမသား",
"မင်းမေဖင်ကြီးသလိုပဲ",
"စောက်တောသားကိုက်ထားမယ်",
"သက်သေမရှိဘဲခွေးလိုအူမနေနဲ့",
"မင်းမေဖာသည်မငါလိုး",
"ဟျောင့်ခွေးမသား",
"မင်းမေစပ့လားအဲတာ",
"ဘာတွေ‌တင်ပြနေတာလဲ",
"အေ့ခွေးစကားပြောတာလား",
"ဆက်ကိုက်ထား",
"စောက်တောသားကိုက်ထားမယ်",
"မင်းမေလိုးပြလေ",
"မသိချင်ဘူးဖာပျက်မသား",
"မင်းမေသေလို့လား",
"အူတူတူနဲ့ငါလိုးမသား",
"ဘာလို့အပျက်ဆန်နေတာလဲစောက်ခွေး",
"လူဖြစ်အရှုံးပေးနေရပီးလားငပေါ",
"အတာဆိုဆက်သာကိုက်ဖာသည်မသားလေး",
"တုံးကျော်မ",
"မင်းကိုခေါ်နေတာ ငိုင်ငိုင်ကြီး ရပ်ကြည့်မနေနဲ့",
"စိတ်မဆိုးပါနဲ့ ဘရားသားအမေကျတော်အတည်မလိုးပါဘူး",
"ကျုပ်ကစတာ ခင်ဗျားက စိတ်ဆိုးပြီး ကိုယ်မေကိုလိုးတော့မလို့လား🤧🤧",
"ဟျောင့် အီညှပ်အီညှပ်နဲ့ငါလိုးမသား ငါ့ဖိနပ်နဲ့ လေဟာနယ်ကြားမှာမင်းပါးနယ်နိမိတ်ခံသွားချင်လား",
"အကုသိုလ် နဲ့ ယှဥ်ဖိုက်လာတဲ့ကောင်ကို အကုသိုလ် လာပေးနေတယ်🤧",
"ဘာတွေခွေးစကားပြော",
"သနားစာတင်ပြတာလားအဲတာ",
"ငါလိုးမစောက်နု",
"ဘာတွေလျှောက်ဆဲနေခွေးဖ",
"ကိုက်ပါလားတပည့်",
"ရေးလေဖာသည်မသား",
"ခွေးမျိုးရိုးကတောခွေးကိုက်လေ",
"ဟျောင့်စောက်ဖားလီးဖြစ်လား",
"ကိုက်ထားပါဟဘာညောင်းတာ",
"မြန်မြန်ကိုက်ဟဖာသည်မသား",
"ပြေးချင်ပီးလားစောက်ရူး",
"စောက်အသုံးမကျတဲ့ဖာသည်မသား",
"စောက်ရူးမင်းလိုခွေးကိုမသနားဘူး",
"လူလိုလိုခွေးလိုလိုရောမချနဲ့",
"ကုလားဘာတွေစဉ်းစားနေတာလဲ",
"မင်းမေကိုခွေးလိုးပီးလား",
"မင်းမိဘမင်းတက်လိုးမအေလိုး",
"ဖျံမကျနဲ့ တစ်ဆင့်ခြင်းဆီကိုက်",
"ငါကိုမနိုင်လို့ကျတဲ့မျက်ရည်လား",
"စောကိခွက်လာမပြောင်နဲ့ဖာသည်မသား",
"ဘရားသား အမေကို စည်းချက်ဝါးချက် ညီညီ အိုးစည်ဗုံမောင်း တီးပြီး အတူတကွ ယှဥ်တွဲပြီး လိုးကြပါစို့",
"စိတ်ဓာတ်ကျ နေမပါနဲ့ ဘရားသားရာ ဘရာသားအမေ တစ်နေ့ဖာသည်မ ဖြစ်မှာပါ",
"မာန်ကိုတင်းထား ခံစားချက်တွေအရမ်းမမြင့်နဲ့ စိတ်ခြောက်ခြားသွားမယ်",
"ကြောက်ပါပြီလို့ မျက်လုံးကိုကြည့်ပြောလေ ကျုပ်ဘောကို ကြည့်မနေနဲ့",
"မသနားဘူးဘောမကိုက်ထား",
"ဖာသည်မသားတပည့်အစုတ်ပလုတ်ကောင်",
"၁ ၂ ၃ ရပြီကိုက်တော့",
"မင်းအမေဘယ်သူလိုးသွားတာ",
"စာတွေမှားကုန်ပီ ကြောက်နေတာလား",
"မင်းအမေ ဖာသည်မကြီးသေတာဆို",
"သေချာကိုက်ကွာ",
"နှမလိုးဘာဖြစ်တာ",
"စိတ်တော့မဆိုးနဲ့ငါ့ကမင်းအမေဖာသည်မရဲ့လင်ပါ",
"မအေလိုး‌ခွေး",
"ဟလီးလားကိုက်လေတပည့်",
"ကိုက်ထားကိုယ်လူရေ",
"ကိုမေကိုလိုးဂါနေတာလား",
"ကြောင်တောင်တောင်နဲ့မအေလိုး",
"လမ်းမှာတွေ့ရင် နှုတ်မဆက်နဲ့ ဘရားအမေကို ကျုပ်ကလိုးမိလိမ့်မယ်",
"စိတ်မဆိုးပါနဲ့ ဘရားသားအမေကျတော်အတည်မလိုးပါဘူး",
"မသိတာကို သိအောင်လုပ် မသိတာမသိမရှိမှ လူရာဝင်မှာ အခုက ဘရားသားရဲ့ ခွေးနောက်ဆုံးအဆင့်",
"ပျင်းလိုက်တာ ဘရားသားအမေကို ရေနွေးဖျော အမွှေးနှုတ် အချဥ်လေးနဲ့ တို့စားကြည့်မယ်",
"ဘရားသား အမေက ကျုပ်အတွက်တော့ ပူဇော်သက္ကာ ထက်မပိုပါဘူး",
"ခွေးဖကခွေးဖစ်ပိးအကိုက်မသန်",
"ရိုက်ဖားပျော့ချက်",
"အဆဲခံရတာပျော်နေပုံပဲ",
"ကုလားကိုက်ဖို့စဉ်းစားထား",
"မအေလိုးကနုတာ",
"မနာလိုတာလား",
"အာခံတာလား",
"အမြန်ဆုံးဆုမင်းမေပေးလိုးမလားး",
"မင်းမေဖင်ကြီးသလိုပဲ",
"မအေလိုးငပျော့ကြီးဆဲရတာလက်ပန်းကျနေပြီလား",
"မင်း ငါဆရာခင်အရှေ့ကြရင် ငြိမ်ကုတ်နေအောင် အဆဲခံရတာပဲလား👉😂",
"အင်းပါ သိလိုက်ပါပြီသင်ဟာဖာသည်မသား😱",
"ဖာသည်မ နင်မပြောနဲ့ နင်ပြောတာက ခွေးကိုက်တာနဲ့အတူတူပဲ",
"ဟျောင့်နှမလိုး မင်းမေစဖုတ်ကိုပရုတ်ဆီတွေထည့်ပြီး လိုးပြီ",
"ငါကြမ်းပြီဆိုမှ ဖေဖေကယ်ပါမေမေကယ်ပါ မလုပ်ရဘူးနော်😂",
"ကျောက်တုံးအက်ကွဲကြောင်းက ထွက်လာတဲ့ ငရူးမျောက်ဝံမ",
"ငါနိုင်ပီ",
"ဖားတာလား",
"ပိတ်လိုးပစ်မယ်",
"မာမူလိုးတာမင်းအမဖြစ်နေလို့",
"လောင်ပြ",
"စကားမများနဲ့ကိုက်",
"ငါကအရမ်းကြမ်းတယ်ပေါ့",
"စတာပါကွ တပည့်ရ မင်းကိုအခုရိုက်နေတာ ဘာပညာမှတောင်မထည့်ဘူး သာမန်လေးဘဲရှိတယ် ဒါတောင်မနိုင်ဘူးလား ဟား",
"မင်းကိုဆဲရတာရော စရတာပင်ပန်းလာပြီ တပည့်ရာ မသိရင် ဝက်စာကျွေးနေရသလိုဘဲ",
"ငါ့ကိုမနိုင်ဘဲအာခံနေတာ ငါထုတ်သုံးတဲ့ပညာတွေကို မှတ်ထားပြီး ခိုးကျင့်နေတယ်မလား ပညာမဲ့ဝက်ရ",
"ဘာသင်ပေးရမလည်းတပည့် ငါ့ဆီက ပညာတွေ မခိုးနဲ့ငါကရက်ရောတယ် မင်းကဝက်ဆိုရင်တောင် အသက်အောင့်ပြီး စောက်ခွက်ကိုနင်းပေးပါတယ်",
"မင်းကိုသနားလာပြီတပည့်ရာ အဲ့လောက်တောင်ငါ့ကိုအနိုင်လိုချင်တာလား ဒါဆို မင်းကိုလီးကြီးထောင်ပေးမယ် ယူလိုက်တပည့်",
"ငါလိုးမသား",
"ညောင်းမနေနဲ့ထထအလုပ်လုပ်",
"ကြောင်နေတာလား",
"ဖာသည်မသား ကြွက်လိုးမသား",
"ဘောမ",
"စောက်ဝက်သားဖက် မင်းကနုတယ် ပါးလွန်းလို့ ငါ့ပြောလိုက်တဲ့စကားတစ်လုံးနဲ့တောင်လွင့်သွားနိုင်တယ်",
"မင်းငယ်ရွယ်တဲ့အချိန်တုန်းက ဝက်ပေါကြီးလုပ်ခဲ့တာထင်တယ် အခုကြီးလာတော့ ဝက်ငပေါကြီးဖြစ်နေပြီ တပည့်",
"တော်ကြာတပည့်လေး ဝက်သားနီလွန်ရင်း အသက်ထွက်သွားအုန်းမယ် ဟား",
"ဖာသည်မသား စောက်ရူးကြီး",
"ဖာသည်မသား လိပ်ဖင်ချမသား",
"ဖာသည်မသား လိပ်လားမင်းက",
"ဖာသည်မသား ငိုထား",
"စောက်ရူးမသား",


]


async def target_reply_loop(chat_id, user_id):
    """စာသားသီးသန့်ဖြင့် မရပ်မချင်း ဇတ်တိုက် Reply ထောက်၍ Loop ပတ်မည့် စနစ်"""
    global IS_FLOODED
    try:
        while True:
            if IS_FLOODED:
                await asyncio.sleep(2)
                continue

            loop_data = running_loops.get(chat_id)
            if not loop_data or user_id not in loop_data["targets"]:
                break

            target = loop_data["targets"][user_id]
            if not target["active"] or not target["msg_ids_pool"]:
                break

            pool = target["msg_ids_pool"]
            pool_idx = target["current_pool_idx"]
            
            if pool_idx >= len(pool):
                pool_idx = len(pool) - 1
                target["current_pool_idx"] = pool_idx

            reply_to_msg_id = pool[pool_idx]

            # [စနစ်သစ်-၁] စာမပို့ခင် တစ်ဖက်လူရဲ့ စာ ID က တကယ်ရှိသေးရဲ့လား အသေအချာစစ်ဆေးခြင်း
            try:
                check_msg = await client.get_messages(chat_id, ids=int(reply_to_msg_id))
                # အကယ်၍ တစ်ဖက်လူက ဖျက်လိုက်ပြီဆိုလျှင်
                if not check_msg or isinstance(check_msg, tl.types.MessageEmpty):
                    # ၎င်းစာနှင့် တွဲထားဖူးသော Bot ၏ Reply စာကို ရှာဖွေပြီး Auto လိုက်ဖျက်ခြင်း
                    del_id_str = str(reply_to_msg_id)
                    if del_id_str in target["msg_map"]:
                        bot_msg_id = target["msg_map"][del_id_str]
                        print(f"[အော်တိုစစ်ဆေးချက်] တစ်ဖက်လူက စာ ID {del_id_str} ကိုဖျက်ထားသဖြင့် Bot ၏ Reply ID {bot_msg_id} ကို လိုက်ဖျက်ပေးလိုက်သည်။")
                        try:
                            await client.delete_messages(chat_id, [bot_msg_id])
                        except Exception:
                            pass
                        del target["msg_map"][del_id_str]

                    if reply_to_msg_id in pool:
                        pool.remove(reply_to_msg_id)
                    
                    if pool:
                        target["current_pool_idx"] = len(pool) - 1
                    else:
                        target["active"] = False
                        break
                    continue
            except FloodWaitError as e:
                async with FLOOD_LOCK:
                    IS_FLOODED = True
                print(f"Telegram Limit ကြောင့် အဝိုင်းလည်သွားသဖြင့် {e.seconds} စက္ကန့် တိတိ ဒဏ်ကြေးငြိမ်စောင့်နေပါသည်...")
                await asyncio.sleep(e.seconds + 2)
                async with FLOOD_LOCK:
                    IS_FLOODED = False
                continue
            except Exception:
                target["active"] = False
                break

            if target["current_pool_idx"] < len(pool) - 1:
                target["current_pool_idx"] += 1

            idx = target["current_idx"]
            msg_to_send = insult_messages[idx % len(insult_messages)]
            target["current_idx"] += 1

            current_delay = loop_data["delay"]
            typing_duration = min(1.0, current_delay / 2)
            remaining_sleep = current_delay - typing_duration

            try:
                # 1. Typing Effect ပြခြင်း
                async with client.action(chat_id, "typing"):
                    if typing_duration > 0:
                        await asyncio.sleep(typing_duration)
                    
                    # 2. စာသားသက်သက်ကိုသာ Reply ထောက်ပြီး ပို့ခြင်း
                    sent_msg = await client.send_message(
                        chat_id, 
                        msg_to_send, 
                        reply_to=int(reply_to_msg_id)
                    )
                    # ID တွဲမှတ်ခြင်း
                    target["msg_map"][str(reply_to_msg_id)] = sent_msg.id

                if remaining_sleep > 0:
                    await asyncio.sleep(remaining_sleep)

            except FloodWaitError as e:
                async with FLOOD_LOCK:
                    IS_FLOODED = True
                print(f"Telegram Limit ကြောင့် အဝိုင်းလည်သွားသဖြင့် {e.seconds} စက္ကန့် တိတိ ဒဏ်ကြေးငြိမ်စောင့်နေပါသည်...")
                await asyncio.sleep(e.seconds + 2)
                async with FLOOD_LOCK:
                    IS_FLOODED = False
                
            except PeerFloodError:
                print("PeerFlood မိသဖြင့် ၁၅ စက္ကန့် စောင့်ဆိုင်းနေပါသည်...")
                await asyncio.sleep(15)
                
            except Exception:
                await asyncio.sleep(3)

    except asyncio.CancelledError:
        pass


# --- [ can ဖျက်တဲ့ Event မိရင် လိုက်ဖျက်ပေးမည့် စနစ် ] ---
@client.on(events.MessageDeleted())
async def handle_message_deleted(event):
    for chat_id, loop_data in list(running_loops.items()):
        for user_id, target in list(loop_data["targets"].items()):
            
            need_index_reset = False
            for deleted_id in event.deleted_ids:
                # [စနစ်သစ်-၂] ID ကို str ရော int ပါ နှစ်မျိုးလုံးနဲ့ စစ်ဆေးခြင်း
                del_id_str = str(deleted_id)
                
                if del_id_str in target["msg_map"]:
                    bot_msg_id = target["msg_map"][del_id_str]
                    print(f"တစ်ဖက်လူက ၎င်း၏စာ ID {del_id_str} ကိုဖျက်သဖြင့် Bot ၏ Reply စာ ID {bot_msg_id} ကို Auto လိုက်ဖျက်ပေးလိုက်ပါသည်။")
                    
                    try:
                        await client.delete_messages(chat_id, [bot_msg_id])
                    except Exception:
                        pass
                    
                    del target["msg_map"][del_id_str]
                    if del_id_str in target["msg_ids_pool"]:
                        target["msg_ids_pool"].remove(del_id_str)
                        need_index_reset = True
            
            if need_index_reset:
                if target["msg_ids_pool"]:
                    target["current_pool_idx"] = len(target["msg_ids_pool"]) - 1
                    target["active"] = True
                    
                    if not target["task"] or target["task"].done():
                        target["task"] = asyncio.create_task(target_reply_loop(chat_id, user_id))
                else:
                    target["active"] = False


# --- [တစ်ဖက်လူဆီမှ စာအသစ်ဝင်လာလျှင် Pool ထဲသို့ ID ထည့်ပေးမည့် စနစ်] ---
@client.on(events.NewMessage(incoming=True))
async def handle_incoming_new_msg(event):
    if IS_FLOODED:
        return

    chat_id = event.chat_id
    user_id = str(event.sender_id)

    if chat_id in running_loops and user_id in running_loops[chat_id]["targets"]:
        target = running_loops[chat_id]["targets"][user_id]
        new_msg_id = str(event.id)

        await asyncio.sleep(3.0)

        if IS_FLOODED:
            return

        try:
            check_msg = await client.get_messages(chat_id, ids=int(new_msg_id))
            if check_msg and not isinstance(check_msg, tl.types.MessageEmpty):
                
                if new_msg_id not in target["msg_ids_pool"]:
                    target["msg_ids_pool"].append(new_msg_id)
                
                target["current_pool_idx"] = len(target["msg_ids_pool"]) - 1
                
                if not target["active"]:
                    target["active"] = True
                    if target["task"]:
                        target["task"].cancel()
                    target["task"] = asyncio.create_task(target_reply_loop(chat_id, user_id))
        except Exception:
            pass


# --- [Bot Commands များ ထိန်းချုပ်မည့် စနစ်] ---
async def extract_user_ids_from_tags(event):
    extracted_ids = []
    text = event.text.strip() if event.text else ""
    if event.entities:
        for entity in event.entities:
            if isinstance(entity, (tl.types.MessageEntityMentionName, tl.types.InputMessageEntityMentionName)):
                extracted_ids.append(str(entity.user_id))
            elif isinstance(entity, tl.types.MessageEntityMention):
                mention_str = text[entity.offset : entity.offset + entity.length]
                try:
                    peer_id = await client.get_peer_id(mention_str)
                    extracted_ids.append(str(peer_id))
                except Exception:
                    pass
    usernames = re.findall(r"@\w+", text)
    for u_name in usernames:
        try:
            peer_id = await client.get_peer_id(u_name)
            extracted_ids.append(str(peer_id))
        except Exception:
            pass
    return extracted_ids


@client.on(events.NewMessage(incoming=False))
async def handle_commands(event):
    global GLOBAL_DELAY
    chat_id = event.chat_id
    text = event.text.strip() if event.text else ""

    if re.match(r"^delay \d+$", text, re.IGNORECASE):
        new_delay = int(text.split()[1])
        GLOBAL_DELAY = new_delay
        if chat_id in running_loops:
            running_loops[chat_id]["delay"] = new_delay
        await event.delete()
        return

    if text == "တောသားဟဟ" or text == "တောသားဟဟ။":
        if chat_id in running_loops:
            for u_id, target in running_loops[chat_id]["targets"].items():
                if target["task"]:
                    target["task"].cancel()
            del running_loops[chat_id]
        await event.delete()
        return

    clean_text = re.sub(r"\[.*?\]\(.*?\)|<.*?>|@\w+", "", text).strip()

    if "သခေါ" in text and clean_text == "သခေါ":
        targets_to_remove = await extract_user_ids_from_tags(event)
        if targets_to_remove or event.is_reply:
            await event.delete()
            
            if event.is_reply and not targets_to_remove:
                reply_msg = await event.get_reply_message()
                if reply_msg and reply_msg.sender_id:
                    targets_to_remove.append(str(reply_msg.sender_id))

            if chat_id in running_loops:
                for u_id in targets_to_remove:
                    if u_id in running_loops[chat_id]["targets"]:
                        if running_loops[chat_id]["targets"][u_id]["task"]:
                            running_loops[chat_id]["targets"][u_id]["task"].cancel()
                        del running_loops[chat_id]["targets"][u_id]
                if not running_loops[chat_id]["targets"]:
                    del running_loops[chat_id]
        return

    if text == "ဝက်မဲ" and event.is_reply:
        await event.delete()
        
        reply_msg = await event.get_reply_message()
        if not reply_msg or not reply_msg.sender_id:
            return

        user_id = str(reply_msg.sender_id)
        first_msg_id = str(reply_msg.id)

        if chat_id not in running_loops:
            running_loops[chat_id] = {
                "delay": GLOBAL_DELAY,
                "targets": {}
            }

        if user_id not in running_loops[chat_id]["targets"]:
            running_loops[chat_id]["targets"][user_id] = {
                "msg_ids_pool": [first_msg_id],
                "current_pool_idx": 0,
                "current_idx": 0,
                "msg_map": {},
                "active": True,
                "task": None
            }
        else:
            if first_msg_id not in running_loops[chat_id]["targets"][user_id]["msg_ids_pool"]:
                running_loops[chat_id]["targets"][user_id]["msg_ids_pool"].append(first_msg_id)
            running_loops[chat_id]["targets"][user_id]["current_pool_idx"] = len(running_loops[chat_id]["targets"][user_id]["msg_ids_pool"]) - 1
            running_loops[chat_id]["targets"][user_id]["active"] = True

        if running_loops[chat_id]["targets"][user_id]["task"]:
            running_loops[chat_id]["targets"][user_id]["task"].cancel()

        task = asyncio.create_task(target_reply_loop(chat_id, user_id))
        running_loops[chat_id]["targets"][user_id]["task"] = task
        return


print("Perfect 100% Auto-Delete Fixed Bot စတင်ပါပြီ...")
client.start()
client.run_until_disconnected()
