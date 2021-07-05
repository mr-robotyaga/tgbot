import logging
import asyncio
import os

from aiogram import Bot, Dispatcher, executor, types
from sqlighter import SQLighter
from aiogram.dispatcher.filters import Command
from aiogram.utils.callback_data import CallbackData
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from googleapiclient.discovery import build


API_TOKEN = '1879123463:AAGdrTHZJgY51ScnXU87MgyYW-T4zK_rEPE'
# задаем уровень логов
logging.basicConfig(level = logging.INFO)
# инициализируем бота
bot = Bot(token = API_TOKEN)
dp = Dispatcher(bot)
# инициализируем соединение с БД
db = SQLighter('database.db')

api_key = 'AIzaSyBLa6Yp_7P2GnJpfn56FPW_cXGWKBShABo'
youtube = build('youtube', 'v3', developerKey = api_key)
playlists = {
	'Криминальная Россия': {
		'Кузьма': 'PLvVbsHajgbLKPFLja1D1TrIWBJmsRyNQc',
		'Антон Власов': 'PLQqzqhE7E32R5qI8Fy8VudX8GL084nwaa'
	}
}

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.answer("Привет!")


@dp.message_handler(commands = ['subscribe'])
async def subscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его
		db.add_subscriber(message.from_user.id, message.from_user.full_name)
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, message.from_user.full_name, True)
	
	await message.answer("Вы успешно подписались на бота!\nМожете просмотреть текущую музыку командой /music")


@dp.message_handler(commands = ['unsubscribe'])
async def unsubscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
		db.add_subscriber(message.from_user.id, message.from_user.full_name, False)
		await message.answer("Вы итак не подписаны.")
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, message.from_user.full_name, False)
		await message.answer("Вы успешно отписались от бота.")

@dp.message_handler(commands = ['addchannel'])
async def addchannel(message: types.Message):
	await message.answer('Чтобы добавить ютуб канал, введите id после слова \'Add\' (регистр не важен)\nПример:\nadd UC6S1hSjVMFbB9WKv-qZKwuw\n\nЧтобы получить id, перейдите на канал\nПример: для канала https://www.youtube.com/channel/UCb6mvPVS9hxJESNROQTnV4Q, id = UCb6mvPVS9hxJESNROQTnV4Q')




@dp.message_handler(commands = ['list'])
async def list(message: types.Message):
	channels = db.get_user_channels(message.from_user.id)
	# l = db.get_user_channels(message.from_user.id)
	# keyboard = InlineKeyboardMarkup()
	# button_list = [types.InlineKeyboardButton('Удалить', callback_data=str(x)) for x in l]
	# keyboard.add(*button_list)
	answer = ''
	for channel in channels:
		answer += channel + '\n'
	await message.answer(answer)


@dp.message_handler(content_types = ['text'])
async def get_text_messages(message: types.Message):

	'''Добавление канала'''
	if message.text.lower().startswith('add'):
		id = message.text[4:]
		request = youtube.channels().list(
			part = "snippet, contentDetails, statistics",
			id = id
		)
		response = request.execute()
		name = response['items'][0]['snippet']['title']
		video_count = response['items'][0]['statistics']['videoCount']
		subscribers =  response['items'][0]['statistics']['subscriberCount']

		'''Если каналa не существует в базе то добавляем, иначе обновляем'''
		if not db.channel_exists(id):
			db.add_channel(name, id, video_count)
		else:
			db.update_channel(id, video_count, subscribers)

		'''Если у пользователя нет канала, то добавляем, иначе ничего не делаем'''
		if not db.user_has(id, message.from_user.id):
			db.add_to_user(name, message.from_user.id)
			await bot.send_message(message.from_user.id, 'Канал успешно добавлен :)')
		else:
			await bot.send_message(message.from_user.id, 'Канал уже добавлен :(')
			
	'''Удаление канала'''	
	if message.text.lower().startswith('delete id'):
		id = message.text[10:]

		'''Если у юзера есть канал, то удаляем его, иначе ничего'''
		if db.user_has(id, message.from_user.id):
			channel = db.delete_from_user(id, message.from_user.id)
			await bot.send_message(message.from_user.id, 'Вы успешно удалили канал {0} :)'.format(channel))
		else:
			await bot.send_message(message.from_user.id, 'У вас нет такого канала :(')


# @dp.message_handler(commands = ['video'])
# async def default_test(message):
#     keyboard = types.InlineKeyboardMarkup()
#     url_button = types.InlineKeyboardButton("Криминальная Россия")
#     keyboard.add(url_button)
#     await bot.send_message(message.chat.id, "В данный момент вы можете просмотреть следующие категории", reply_markup=keyboard)


ids = db.get_all_channels()

for id in range(0, len(ids)):
	request = youtube.channels().list(
		part = "snippet, contentDetails, statistics",
		id = ids[id][0]
	)
	response = request.execute()
	db.update_video_count(ids[id][0], int(response['items'][0]['statistics']['videoCount']))

async def scheduled(wait_for):
	while True:
		await asyncio.sleep(wait_for)
		ids = db.get_all_channels()

		for id in range(0, len(ids)):
			request = youtube.channels().list(
				part = "snippet, contentDetails, statistics",
				id = ids[id][0]
			)
			response = request.execute()
			#print(response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
			counter = db.get_video_count(ids[id][0])
			if counter < int(response['items'][0]['statistics']['videoCount']):
				request = youtube.playlistItems().list(
					part = 'contentDetails, snippet',
					playlistId = response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
					maxResults = 25
				)
				response = request.execute()
				video_id = response['items'][0]['contentDetails']['videoId']
				link = 'https://www.youtube.com/watch?v={0}&list={1}'.format(video_id, ids[id])
				title = response['items'][0]['snippet']['title']
				#data = response['items'][0]['snippet']['publishedAt'].replace('T', ' ').replace('Z', '')
				photo = response['items'][0]['snippet']['thumbnails']['maxres']['url']
				
				for subscriber in db.get_subscriptions():
					if db.get_status(subscriber[1]):
						button = types.InlineKeyboardButton(text = "Перейти", url = link)
						keyboard = types.InlineKeyboardMarkup(row_width=1)
						keyboard.add(button)
						await bot.send_photo(subscriber[1], photo, caption = title, reply_markup=keyboard)
				db.increase_video_count(ids[id][0], counter)
		# subscriptions = db.get_subscriptions()
		# for s in subscriptions:
		# 	await bot.send_message(s[1], "Привет!\nТы здесь не один)")
		# def add_videos(playlist_id):
		# 	request = youtube.playlistItems().list(
		# 		part = 'contentDetails, snippet',
		# 		# forUsername = 'KuzyaMeduzya'
		# 		playlistId = playlist_id,
		# 		maxResults = 50
    	# 	)		
		# 	response = request.execute()
		# 	videos = len(response['items'])
		# 	for video in range(0, videos):
		# 		request = youtube.videos().list(
		# 			part = "snippet, contentDetails, statistics",
		# 			id = response['items'][video]['contentDetails']['videoId']
		# 		)
		# 		data = request.execute()
		# 		if not db.video_exists(response['items'][video]['contentDetails']['videoId']):
		# 			if playlist_id in playlists['Криминальная Россия'].values():
		# 				programm = 'Криминальная Россия' 
		# 			else:
		# 				programm = ''
		# 			duration = data['items'][0]['contentDetails']['duration'].replace('PT', '').replace('H', ':').replace('M', ':').replace('S', '')
		# 			title = data['items'][0]['snippet']['title'].replace('КРИМИНАЛЬНАЯ РОССИЯ - ', '')
		# 			link = 'https://www.youtube.com/watch?v={0}&list={1}'.format(str(response['items'][video]['contentDetails']['videoId']), playlist_id)
		# 			video_id = response['items'][video]['contentDetails']['videoId']
		# 			date = data['items'][0]['snippet']['publishedAt'].replace('T', ' ').replace('Z', '')
		# 			views = data['items'][0]['statistics']['viewCount']
		# 			likes = data['items'][0]['statistics']['likeCount']
		# 			dislikes = data['items'][0]['statistics']['dislikeCount']
		# 			db.add_video(title, programm, link, video_id, date, duration, views, likes, dislikes)
		# 			#print('Video has been added successfully')
		# 			continue
		# 		else:
		# 			request = youtube.videos().list(
		# 					part = "snippet, contentDetails, statistics",
		# 					id = response['items'][0]['contentDetails']['videoId']
		# 				)
		# 			data = request.execute()
		# 			if playlist_id in playlists['Криминальная Россия'].values():
		# 				programm = 'Криминальная Россия'
		# 			else:
		# 				programm = ''
		# 			title = data['items'][0]['snippet']['title'].replace('КРИМИНАЛЬНАЯ РОССИЯ - ', '')
		# 			link = 'https://www.youtube.com/watch?v={0}&list={1}'.format(str(response['items'][0]['contentDetails']['videoId']), playlist_id)
		# 			video_id = response['items'][0]['contentDetails']['videoId']
		# 			date = data['items'][0]['snippet']['publishedAt'].replace('T', ' ').replace('Z', '')
		# 			duration = data['items'][0]['contentDetails']['duration'].replace('PT', '').replace('H', ':').replace('M', ':').replace('S', '')
		# 			views = data['items'][0]['statistics']['viewCount']
		# 			likes = data['items'][0]['statistics']['likeCount']
		# 			dislikes = data['items'][0]['statistics']['dislikeCount']
		# 			db.update_video(views, likes, dislikes, video_id)
		# 			#print('Video has been updated successfully')
		# add_videos(playlists['Криминальная Россия']['Кузьма'])
		# add_videos(playlists['Криминальная Россия']['Антон Власов'])
		# request = youtube.playlistItems().list(
		# 		part = 'contentDetails, snippet',
		# 		# forUsername = 'KuzyaMeduzya'
		# 		playlistId = playlist_id,
		# 		maxResults = 50
    	# 	)		
		# response = request.execute()
		# last_video = response['items'][0]
		# if not db.video_exists(response['items'][0]['contentDetails']['videoId']): 
			# for subscriber in db.get_subscriptions():
			# 	await bot.send_photo(subscriber[0], )


# запускаем лонг поллинг
if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.create_task(scheduled(10))
	 # пока что оставим 10 секунд (в качестве теста)
	executor.start_polling(dp, skip_updates = True)
