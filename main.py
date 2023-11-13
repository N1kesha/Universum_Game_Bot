from datetime import datetime, timedelta
from copy import deepcopy
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove)
import config as cfg
from db import Database
import sqlite3

sleep_time = 24*60*60

form_router = Router()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=cfg.TOKEN, parse_mode=ParseMode.HTML)
db= Database('database.db')
hint_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Request a hint")]], resize_keyboard=True, one_time_keyboard=True)

right_answers = {1: "Restaurant Tokio", 2: "Ethereum", 3: "Industrial zone", 4: "Boiler House",
                 5: "Night Club Neon Heaven", 6: "10000", 7: "$UM", 8: "Casino", 9: "10", 10: "250"}
mistakes_ans = {1: f"Excuse me? That's the wrong answer, but let's pretend we just didn't hear you! "
                f"Try again! Just be extremely careful not to make a mistake a second time and not lose a life..."}
ans1 = {1: f"While walking through the blocks of the metropolis, you found a note with a strange text:\n\n"
        f"«I've hidden the valuables in a secure place. To claim them, head to the restaurant with the most Japanese name in the city and tell "
        f"the bartender that you've come from Alex».\n\n"
        f"Which city building will you go to?\n\n"
        f"P.S. Remember that the names of the buildings should be entered in full and exactly as they are written in the WhitePaper on our website. "
        f"For example, Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop.",
        2: f"Correct!\n\nRestaurant Tokio is an authentic Japanese restaurant with a classic, seafood-rich cuisine that amazed "
        f"you with its interior and ambiance.\n\nLooking around, you noticed the bar, approached, and, waiting for the "
        f"bartender to notice you, whispered softly: “I'm from Alex“.\n\n"
        f"The bartender squinted, looking you directly in the eyes, and said:\n\n"
        f"Then you must know the passphrase. It's the blockchain used for minting NFTs in Universum...\n\n "
        f"What answer will you give?",
        3: f"It seems you made a mistake and lost one life!\nBut it's not all bad: yes, you didn't go where you needed to, "
        f"but you still have the note!\n\nJust try again! Which building will you go to now?\n\n"
        f"P.S. Remember that the names of the buildings should be entered in full and exactly as they are written in the WhitePaper on our website. "
        f"For example, Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop.",
        4: f"It seems that to choose the right establishment, you'll have to visit all the restaurants in the city!\n\n"
        f"But the local waitress took pity on you after hearing the story of how you're looking for the “restaurant with the most "
        f"Japanese name” and advised you to check out the place whose name includes the name of the capital of Japan...\n\n"
        f"Which building will you go to now?\n\n"
        f"P.S. Remember that the names of the buildings should be entered in full and exactly as they are written in the "
        f"WhitePaper on our website. For example, Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop."}
ans2 = {1: f"Upon hearing your answer, the bartender nodded in approval and pulled a key out of his pocket, "
        f"handing it to you.\n\n- So where should I look for the door that this key opens? - you asked.\n\n"
        f"- I have no idea, - shrugged the bartender.\n- All I know is that the building is somewhere in the "
        f"area of factories, power plants, and such. It seems like you need the most common building in that area. "
        f"Well, you'll have to search on your own. Which City Zone will you head to?\n\n"
        f"P.S. Remember that the zone name should be entered in full and exactly as the zone is named in the "
        f"WhitePaper on our website.",
        2: f"The bartender let out a disappointed sigh, and by the look on his face, you immediately realized you gave the wrong answer.\n\n"
           f"- Wait, - you hurriedly mumbled faster than he lost interest in you.\n"
           f"- I just misspoke! I meant...\n\n"
           f"On which blockchain is the minting of NFTs conducted in Universum?",
        3: f"Again, a miss!\n\nThe bartender didn't say anything, but from his look, you sensed that you had another chance. "
           f"Perhaps your nervousness played in your favor, and he allowed for the possibility that you simply made a mistake. "
           f"Or maybe he just liked you...\n\n- Well? - he urged you.\n\n"
           f"- The most common blockchain for decentralized applications... digital silver... a stable second on CoinMarketCap...\n\n"
           f"- It's...\n\nWhat answer will you give?"}
ans3 = {1: f"The Industrial zone greeted you with modern high-tech buildings, and you almost got lost in them. "
           f"Remembering the bartender's words about finding the most common building in this area, you felt more confident "
           f"and headed towards...\n\nWhich building did you head towards?\n\n"
           f"P.S. Remember that the names of the buildings should be entered in full and exactly as they are written in the "
           f"WhitePaper on our website. For example, Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop.",
        2: f"Once again, not the right place!\n\nThe zone you ended up in looks nothing like the place the bartender described: "
           f"there are no factories or power plants here... It's a good thing you still have time and can continue wandering "
           f"around the city!\n\nWhich City Zone will you head to now?\n\nP.S. Remember that the zone name should be entered in "
           f"full and exactly as the zone is named in the WhitePaper on our website.",
        3: f"Are you serious? It seems like you've found an analogue of the Bermuda Triangle in our metaverse! How else can you "
           f"explain the fact that in a city where there aren't that many different zones, you keep missing the right one?\n\n"
           f"Well, let's try again: which City Zone will you head to now?\n\n"
           f"P.S. Remember that the zone name should be entered in full and exactly as the zone is named in the WhitePaper "
           f"on our website."}
ans4 = {1: f"Your knowledge and luck didn't deceive you!\n\nThe key did fit the door of the Boiler House, and as it swung open, "
           f"you saw the coveted case on the floor...\n\nBut it wasn't that simple - inside it, you found another note instructing "
           f"you to go to a nightclub. Below, it was noted that you should choose the club valued at 10 points.\n\n"
           f"Where will you head?\n\nP.S. Remember that the names of the buildings should be entered in full and exactly "
           f"as they are written in the WhitePaper on our website. For example, Coffee Shop Cappuccino, not just Cappuccino, "
           f"and not Coffee Shop.",
        2:f"It seems you chose a building that doesn't even have a lock on the door, so you won't be able "
          f"to open it with your key...\n\nTake a look around and try again! Remember, you need the most common "
          f"building in this zone...\n\nWhich building will you head towards?\n\nP.S. Remember that the names of the buildings should be"
          f" entered in full and exactly as they are written in the WhitePaper on our website. For example, Coffee Shop Cappuccino, "
          f"not just Cappuccino, and not Coffee Shop.",
        3: f"Not a bad attempt. This time you even managed to find a door with a lock on the chosen building, but the local "
           f"security guard mistook you for a thief and threatened to call the police if you didn't leave his territory immediately!\n\n"
           f"After stepping back to a safe distance, you once again turned your head in search of the most common building in the area and, "
           f"it seems, finally saw it!\n\nWhich building will you head towards?\n\nP.S. Remember that the names of the buildings should "
           f"be entered in full and exactly as they are written in the WhitePaper on our website. For example, "
           f"Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop."}
ans5 = {1: f"Looks like you've come to the right place!\n\nIn any case, they were already waiting for you here. "
           f"The pretty blonde girl specified that you came from Alex, and then waved her finger somewhere in the VIP zone.\n\n"
           f"- I have something for you! - she chirped. - But I'm not giving it away for nothing! I want you to pay me as much "
           f"as the total number of NFTs City Blocks in the Universum metaverse...\n\nWhat number will you give her?\n\n"
           f"P.S. Just enter the number without spaces. For example, 15000",
        2: f"And you don't often hang out in clubs... How do we know?\n\nIt's just that if you were a regular at nightclubs "
           f" in Universum, you probably would have chosen the right establishment from the first attempt, but that didn't happen.\n\n"
           f"You made a mistake and ended up in a completely different place. Maybe you forgot that you need to choose a club "
           f"that is valued at 10 points? Try again!\n\nP.S. Remember that the names of the buildings should be entered in full "
           f"and exactly as they are written in the WhitePaper on our website. For example, Coffee Shop Cappuccino, "
           f"not just Cappuccino, and not Coffee Shop.",
        3: f"You even asked for help from a taxi driver, but he turned out to be an even worse connoisseur of the city than you "
           f"and took you somewhere unknown!\n\nBut perhaps, while you were looking for a bus stop to get out of this area, "
           f"you still figured out which nightclub you were supposed to go to?\n\nP.S. Remember that the names of the buildings "
           f"should be entered in full and exactly as they are written in the WhitePaper on our website. For example, "
           f"Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop."}
ans6 = {1: f"Your offer suited her perfectly, and the girl smiled contentedly. But as soon as you handed her 10,000 USD, "
           f"she wrinkled her nose in disdain and asked:\n\n- Aren't you local? We have a different currency here. Do you at least "
           f"know what it's called?\n\n“Of course I do!” - you hurried to reply, seeing the girl losing interest in you.\n\n"
           f"“And what is it?” - she asked.\n\nWhat will you answer? What is the name of the Universum currency?\n\n"
           f"P.S. Enter the ticker of our token with the $ symbol. Example: $BTC",
        2: f"It seems the amount you suggested to the blonde didn't appeal to her!\nShe wrinkled her nose capriciously and said:\n\n"
           f"- Actually, we agreed on something else...\n\n“We haven't agreed on anything yet,” - you wanted to reply, "
           f"but held back, thinking it would be better to try again and offer the girl the amount she wants.\n\n"
           f"What number will you tell her?\n\nP.S. Just enter the number without spaces. For example, 15000",
        3: f"“You either have a problem with math or with your head!” - the blonde finally became disappointed in your mathematical "
           f"abilities, but you managed to hold her hand before she left.\n\n“I made a mistake,” - you said. "
           f"“I should have immediately offered you...”\n\nWhat number will you tell her?\n\n"
           f"P.S. Just enter the number without spaces. For example, 15000"}
ans7 = {1: f"Finally, the blonde exchanged anger for mercy.\n\nTaking the money, she pulled a plastic gaming chip from her bra "
           f"and handed it to you.\n\n“And what do I do with this?” - you clarified.\n\n“Play with it,” - the blonde smiled, "
           f"getting lost on the dance floor. “You're sure to be lucky at roulette!”\n\nPlay roulette? Why not! "
           f"Especially since there's only one place in the city where you can do it legally!\n\nWhere will you head?\n\n"
           f"P.S. Remember that the names of the buildings should be entered in full and exactly as they are written in the "
           f"WhitePaper on our website. For example, Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop.",
        2: f"“You probably think I'm completely stupid,” - frowned the blonde. “Do you think I don't know that the exchange "
           f"rate of this coin is several times lower than our currency? Do you want to deceive me?”\n\nIt turned out very ugly! "
           f"Now you need to quickly justify yourself and give a different answer!\n\nWhat will you say?\n\nWhat is the name of "
           f"the Universum currency?\n\nP.S. Enter the ticker of our token with the $ symbol. Example: $BTC",
        3: f"The blonde didn't even bother to answer you, she just sighed disappointingly and rolled her eyes, displaying her "
           f"complete disappointment in your knowledge.\n\n“Wait! Give me one more chance!” - you pleaded, and the girl looked "
           f"at you, waiting for an answer to the question, what is the name of the Universum currency?\n\n"
           f"P.S. Enter the ticker of our token with the $ symbol. Example: $BTC"}
ans8 = {1: f"The dealer was very surprised when you sat down at the table and placed the chip on the felt.\n\n"
           f"“Are you from Alex?” - the dealer asked, looking at your chip, which was different from the standard casino chips.\n\n"
           f"You nodded in response, and the dealer clarified, - “Would you like to place a bet?”\n\n"
           f"“Yes...” - you mumbled uncertainly.\n\n- Then I suggest betting on the number corresponding to the number of stages "
           f"on the Universum roadmap, posted on the main page of the official website.\n\nWhich number will you bet on?",
        2: f"And are you sure that the place you came to in Universum is where they play roulette? The locals looked at "
           f"you like a city madman when you pulled out the chip and asked where to find the dealer!\n\nYou need to leave "
           f"before they call the sanitarium! And it's better to go straight to where you can play.\n\nWhich building will you go to?\n\n"
           f"P.S. Remember that the names of the buildings should be entered in full and exactly as they are written in the "
           f"WhitePaper on our website. For example, Coffee Shop Cappuccino, not just Cappuccino, and not Coffee Shop.",
        3: f"But at the very beginning of the quest, a bright thought came to you that you're not too familiar with the city "
           f"and it would be better to have a printed White Paper or at least a city map with you! "
           f"You came to the wrong address again!\n\nWill we continue driving?\n\nWhere in Universum can you play roulette? "
           f"Which building will we go to?\n\nP.S. Remember that the names of the buildings should be entered in full and "
           f"exactly as they are written in the WhitePaper on our website. For example, Coffee Shop Cappuccino, "
           f"not just Cappuccino, and not Coffee Shop."}
ans9 = {1: f"The ball hopped on the roulette and landed on 10...\n\n- Your bet won! - exclaimed the dealer joyfully. "
           f"Pushing your winnings toward you, he added:\n\n- The case you're looking for is here, in the casino. "
           f"It's in the storage room, in locker №10. Just enter the code to retrieve it.\n\n- What code? - you asked, displeased.\n\n"
           f"- The code is the minimum possible City Block Score number at Universum...\n\nWhat number will you enter?",
        2: f"It seems the dealer is rooting for you and genuinely wants you to win!\n\nHow else to explain the fact that "
           f"he pretended not to hear your mistaken bet and continued to patiently look at you, suggesting to name "
           f"a different number!\n\nWhich number will you bet on?",
        3: f"The bet didn't win, but the dealer didn't remove the chip from the felt!\n\nMoreover, he reminded you once "
           f"again that he advises betting on the number corresponding to the number of stages on the Universum roadmap "
           f"posted on the main page of the official website.\n\nWhich number will you bet on?"}
ans10 = {1: f"Congratulations!!!\n\nYou have opened the storage unit and reached the case, which turned out to be unlocked!\n\n"
            f"Now you have access to the treasures hidden here by Alex!\n\n"
            f"Your prize is a Whitelist spot certificate for our project!\n\n"
            f"To claim your reward, join our Discord, open a ticket, and send a screenshot of this message there!\n"
            f"https://discord.com/invite/ARNRwuM7mT\n\n"
            f"Have a great day!",
         2: f"With trembling hands, you entered the code and... nothing happened! It seems you made a mistake and should try again!\n\n"
            f"What number will you enter?",
         3: f"If you had entered the correct code, a green light would have lit up on the storage room door, and for five seconds, "
            f"you could have turned the handle clockwise to open the storage compartment...\n\nBut that didn't happen! "
            f"So, you can try again..."}

lives_dict = {}
hints_dict = {}
freeze_start_time = {}
user_mistakes = {}

# States
class Form(StatesGroup):
    yes = State()
    ans1 = State()
    ans1_after_mistake = State()
    ans2 = State()
    ans2_after_mistake = State()
    ans3 = State()
    ans3_after_mistake = State()
    ans4 = State()
    ans4_after_mistake = State()
    ans5 = State()
    ans5_after_mistake = State()
    ans6 = State()
    ans6_after_mistake = State()
    ans7 = State()
    ans7_after_mistake = State()
    ans8 = State()
    ans8_after_mistake = State()
    ans9 = State()
    ans9_after_mistake = State()
    ans10 = State()
    ans10_after_mistake = State()
    final = State()


class Lives_Counter:
   def __init__(self, bot, user_id):
       self.lives_counter = 3
       self.bot = bot
       self.user_id = user_id
   async def subtract_lives(self, user_id, n):
       self.n = n
       self.user_id = user_id
       if self.lives_counter >= 1:
            self.lives_counter -= n
       if self.lives_counter > 1 or self.lives_counter == 0:
            await self.bot.send_message(user_id, f"You have {self.lives_counter} lives ❤️ left.")
       elif self.lives_counter == 1:
           await self.bot.send_message(user_id, f"You have {self.lives_counter} life ❤️ left.")

   async def add_lives(self, user_id, n):
       self.user_id = user_id
       self.n = n
       self.lives_counter += n
       if self.lives_counter > 1:
           await self.bot.send_message(user_id, f"You have {self.lives_counter} lives ❤️ left.")
       elif self.lives_counter == 1:
           await self.bot.send_message(user_id, f"You have {self.lives_counter} life ❤️ left.")

class Hints_Counter:
    def __init__(self, bot, user_id):
        self.hints_counter = 3
        self.bot = bot
        self.user_id = user_id
    async def subtract_hints(self, user_id, n):
        self.user_id = user_id
        self.n = n
        if self.hints_counter >= 1:
            self.hints_counter -= n
        if self.hints_counter > 1 or self.hints_counter == 0:
            await self.bot.send_message(user_id, f"You have {self.hints_counter} hints 💡️ left.")
        elif self.hints_counter == 1:
            await self.bot.send_message(user_id, f"You have {self.hints_counter} hint 💡 left.")

    async def add_hints(self, user_id, n):
        self.user_id = user_id
        self.n = n
        self.hints_counter += n
        if self.hints_counter > 1:
            await self.bot.send_message(user_id, f"You have {self.hints_counter} hints 💡️ left.")
        elif self.hints_counter == 1:
            await self.bot.send_message(user_id, f"You have {self.hints_counter} hint 💡️️ left.")


@form_router.message(Command("start"))
async def command_start(message: Message, state: FSMContext) -> None:
    user_full_name = message.from_user.full_name
    user_id = message.from_user.id
    if user_id not in lives_dict:
        lives_dict[user_id] = Lives_Counter(bot, user_id)
        hints_dict[user_id] = Hints_Counter(bot, user_id)
    else:
        lives_dict[user_id].lives_counter = lives_dict[user_id].lives_counter
        hints_dict[user_id].hints_counter = hints_dict[user_id].hints_counter

    if not db.user_exists(user_id):
        start_command = message.text
        referrer_id = str(start_command[7:])
        if str(referrer_id) != "":
            if str(referrer_id) != str(user_id):
                db.add_user(user_id, referrer_id)
                try:
                    await bot.send_message(referrer_id, f"A new user has registered using your referral link! So, you earned one life!", reply_markup=hint_markup)
                    await lives_dict[int(referrer_id)].add_lives(int(referrer_id), 1)
                except:
                    pass
            else:
                await bot.send_message(user_id, "You can't register using your own referral link 🙂")
                db.add_user(user_id)
        else:
            pass

    await state.set_state(Form.yes)
    await message.answer(f"In one of the cities of the metaverse Universum, a case with valuables is hidden somewhere.\n\n"
             f"Right now, you have a chance to find it and claim your reward!\n\n{user_full_name}, are you ready to join the game?",
            reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Yes")]], resize_keyboard=True, one_time_keyboard=True))


@form_router.message(Form.yes, F.text.casefold() == "yes")
async def process_yes(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.ans1)
    await message.answer(ans1[1])


@form_router.message(Form.ans1)
async def process_ans1(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "restaurant tokio":
        user_mistakes[user_id] = 0
        await message.reply(ans1[2])
        await state.set_state(Form.ans2)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans1_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans1_after_mistake)
async def process_ans1_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "restaurant tokio":
        user_mistakes[user_id] = 0
        await message.reply(ans1[2])
        await state.set_state(Form.ans2)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[1]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        if user_mistakes[user_id] == 1 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans1[3], reply_markup=hint_markup)
            else:
                await message.reply(ans1[3])

        elif user_mistakes[user_id] >= 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 3
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans1[4],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans1[4])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans1[1 + user_mistakes[user_id]],
                                     reply_markup=hint_markup)

@form_router.message(Form.ans2)
async def process_ans2(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "ethereum":
        user_mistakes[user_id] = 0
        await message.reply(ans2[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans3)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans2_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans2_after_mistake)
async def process_ans2_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "ethereum":
        user_mistakes[user_id] = 0
        await message.reply(ans2[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans3)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[2]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans2[2], reply_markup=hint_markup)
            else:
                await message.reply(ans2[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans2[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans2[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans2[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.ans3)
async def process_ans3(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "industrial zone":
        user_mistakes[user_id] = 0
        await message.reply(ans3[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans4)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans3_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans3_after_mistake)
async def process_ans3_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "industrial zone":
        user_mistakes[user_id] = 0
        await message.reply(ans3[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans4)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[3]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans3[2], reply_markup=hint_markup)
            else:
                await message.reply(ans3[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans3[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans3[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans3[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.ans4)
async def process_ans4(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "boiler house":
        user_mistakes[user_id] = 0
        await message.reply(ans4[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans5)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans4_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans4_after_mistake)
async def process_ans4_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "boiler house":
        user_mistakes[user_id] = 0
        await message.reply(ans4[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans5)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[4]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans4[2], reply_markup=hint_markup)
            else:
                await message.reply(ans4[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans4[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans4[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans4[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.ans5)
async def process_ans5(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "night club neon heaven":
        user_mistakes[user_id] = 0
        await message.reply(ans5[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans6)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans5_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans5_after_mistake)
async def process_ans5_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "night club neon heaven":
        user_mistakes[user_id] = 0
        await message.reply(ans5[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans6)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[5]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans5[2], reply_markup=hint_markup)
            else:
                await message.reply(ans5[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans5[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans5[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans5[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.ans6)
async def process_ans6(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "10000":
        user_mistakes[user_id] = 0
        await message.reply(ans6[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans7)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans6_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans6_after_mistake)
async def process_ans6_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "10000":
        user_mistakes[user_id] = 0
        await message.reply(ans6[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans7)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[6]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans6[2], reply_markup=hint_markup)
            else:
                await message.reply(ans6[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans6[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans6[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans6[user_mistakes[user_id]],
                                     reply_markup=hint_markup)

@form_router.message(Form.ans7)
async def process_ans7(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "$um":
        user_mistakes[user_id] = 0
        await message.reply(ans7[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans8)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans7_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans7_after_mistake)
async def process_ans7_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "$um":
        user_mistakes[user_id] = 0
        await message.reply(ans7[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans8)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[7]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans7[2], reply_markup=hint_markup)
            else:
                await message.reply(ans7[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans7[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans7[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans7[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.ans8)
async def process_ans8(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "casino":
        user_mistakes[user_id] = 0
        await message.reply(ans8[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans9)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans8_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans8_after_mistake)
async def process_ans8_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "casino":
        user_mistakes[user_id] = 0
        await message.reply(ans8[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans9)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[8]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans8[2], reply_markup=hint_markup)
            else:
                await message.reply(ans8[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans8[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans8[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans8[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.ans9)
async def process_ans9(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "10":
        user_mistakes[user_id] = 0
        await message.reply(ans9[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans10)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans9_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans9_after_mistake)
async def process_ans9_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "10":
        user_mistakes[user_id] = 0
        await message.reply(ans9[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.ans10)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[9]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans9[2], reply_markup=hint_markup)
            else:
                await message.reply(ans9[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans9[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans9[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans9[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.ans10)
async def process_ans10(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.text.casefold() == "250":
        user_mistakes[user_id] = 0
        await message.reply(ans10[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.final)
    else:
        user_mistakes[user_id] = 1
        await state.set_state(Form.ans10_after_mistake)
        await message.reply(mistakes_ans[1])


@form_router.message(Form.ans10_after_mistake)
async def process_ans10_after_mistake(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start = datetime.now()
    start_copied = deepcopy(start)
    if message.text.casefold() == "250":
        user_mistakes[user_id] = 0
        await message.reply(ans10[1], reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.final)

    elif message.text.casefold() == "request a hint":
        await hints_dict[user_id].subtract_hints(user_id, 1)
        await message.answer(
            f"Universum is the most advanced metaverse where, of course, there is an AI that knows everything. "
            f"Including the answer to your question!")
        await message.answer(f"<b>Correct answer: {right_answers[10]}</b>", parse_mode=ParseMode.HTML)
        await message.answer(f"Enter the correct answer")
        if hints_dict[user_id].hints_counter == 0:
            await asyncio.sleep(sleep_time)
            hints_dict[user_id].hints_counter = 1

    else:
        await lives_dict[user_id].subtract_lives(user_id, 1)
        user_mistakes[user_id] += 1

        if user_mistakes[user_id] == 2 and lives_dict[user_id].lives_counter > 0:
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans10[2], reply_markup=hint_markup)
            else:
                await message.reply(ans10[2])

        elif user_mistakes[user_id] > 2 and lives_dict[user_id].lives_counter > 0:
            user_mistakes[user_id] = 2
            if hints_dict[user_id].hints_counter > 0:
                await message.reply(ans10[3],
                                    reply_markup=hint_markup)
            else:
                await message.reply(ans10[3])

        elif lives_dict[user_id].lives_counter == 0:
            if user_id not in freeze_start_time.keys():
                freeze_start_time[user_id] = datetime.now()
            revival = freeze_start_time[user_id] + timedelta(hours=24)
            time_left = revival - datetime.now()
            time_left_in_s = time_left.total_seconds()
            hours = int(divmod(time_left_in_s, 3600)[0])
            minutes = int(divmod(time_left_in_s, 3600)[1] / 60)

            await message.answer(
                f"Well, solving riddles doesn't seem to be your forte... But in school, there's always a "
                f"chance for a retake! We won't torture you today — come back in {hours} hours {minutes} minutes and give it another try!")
            await message.answer(f"Or maybe you want to continue the game right away?\n\n"
                                 f"Share the link to this quest with your friends, and we will add one life for each player who joins using your invitation!\n\n"
                                 f"Your personal referral link: https://t.me/{cfg.BOT_NICKNAME}?start={user_id}")

            await asyncio.sleep(sleep_time)

            del freeze_start_time[user_id]
            if lives_dict[user_id].lives_counter == 0:
                lives_dict[user_id].lives_counter = 3
                await message.answer(
                    f"Wow!\nUniversum is indeed rightfully considered one of the most technologically advanced metaverses - yesterday "
                    f"you lost your third life, and today they're already restored!\n\nThe hospital and rescue center staff worked all this "
                    f"time to bring you back to life.\nThey kindly ask you not to waste your lives now.")
                await message.answer(f"You have {lives_dict[user_id].lives_counter} lives ❤️ again!")
                await message.answer(ans10[user_mistakes[user_id]],
                                     reply_markup=hint_markup)


@form_router.message(Form.final)
async def process_final(message: Message, state: FSMContext):
    pass



async def main():
    bot = Bot(token=cfg.TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())