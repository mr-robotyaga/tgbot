import sqlite3
from sqlite3 import Error
from sqlite3.dbapi2 import connect

class SQLighter:

    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = self.createConnection(database)
        self.cursor = self.connection.cursor()
    
    def createConnection(self, path):
        print('Establishing connection with DataBase...')
        connection = None
        try:
            connection = sqlite3.connect(path)
            print("Connection to SQLite DataBase successful\n")
        except Error as e:
            print("The error '{e}' occurred".format(e))

        return connection

    def get_subscriptions(self, status = True):
        """Получаем всех активных подписчиков бота"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM `subscriptions` WHERE `status` = ?", (status,)).fetchall()

    def subscriber_exists(self, user_id):
        """Проверяем, есть ли уже юзер в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `subscriptions` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def get_status(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT `status` FROM `subscriptions` WHERE `user_id` = ?', (user_id,)).fetchall()[0][0]
            return bool(result)

    def add_subscriber(self, user_id, user_name, status = True):
        """Добавляем нового подписчика"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `subscriptions` (`user_id`, `status`, `name`) VALUES(?,?,?)", (user_id, status, user_name))

    def update_subscription(self, user_id, user_name, status):
        """Обновляем статус подписки пользователя"""
        with self.connection:
            return self.cursor.execute("UPDATE `subscriptions` SET `status` = ?, `name` = ? WHERE `user_id` = ?", (status, user_name, user_id))



    def add_video(self, title, programm, link, video_id, date, duration, views = 0, likes = 0, dislikes = 0):
        """Добавляем новое видео"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `videos` (`title`, `programm`, `link`, `video_id`, `date`, `duration`, `views`, `likes`, `dislikes`) VALUES(?,?,?,?,?,?,?,?,?)", (title, programm, link, video_id, date, duration, views, likes, dislikes))

    def video_exists(self, video_id):
        """Проверяем, есть ли уже видео в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `videos` WHERE `video_id` = ?', (video_id,)).fetchall()
            return bool(len(result))
    
    def update_video(self, views, likes, dislikes, video_id):
        """Обновляем видео"""
        with self.connection:
            return self.cursor.execute("UPDATE `videos` SET `views` = ?, `likes` = ?, `dislikes` = ? WHERE `video_id` = ?", (views, likes, dislikes, video_id))

    def get_videos(self, programm):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `videos` WHERE `programm` = ?", (programm,)).fetchall()



    def channel_exists(self, channel_id):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `channels` WHERE `channel_id` = ?', (channel_id,)).fetchall()
            return bool(len(result))

    def add_channel(self, name, channel_id, video_count):
        """Добавляем новый канал"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `channels` (`name`, `channel_id`, `video_count`) VALUES(?,?,?)", (name, channel_id, video_count))

    def user_has(self, channel_id, user_id):
        with self.connection:
            name = self.cursor.execute("SELECT `name` FROM `channels` WHERE `channel_id` = ?", (channel_id,)).fetchall()
            user_channels = self.cursor.execute("SELECT `channels` FROM `subscriptions` WHERE `user_id` = ?", (user_id,)).fetchall() 
            if name[0][0] in user_channels[0][0]:
                return True

    def add_to_user(self, name, user_id):
        with self.connection:
            all = self.cursor.execute("SELECT `channels` FROM `subscriptions` WHERE `user_id` = ?", (user_id,)).fetchall()
            user = self.cursor.execute("SELECT `name` FROM `subscriptions` WHERE `user_id` = ?", (user_id,)).fetchall()
            result = ''
            if not all[0]:
                for i in all[0]:
                    result += str(i) + ', '
                result += name
            else:
                result = name
            print(result + ' has been added to ' + user[0][0] + '(' + str(user_id) + ')')
            return self.cursor.execute("UPDATE `subscriptions` SET `channels` = ? WHERE `user_id` = ?", (result, user_id))

    def delete_from_user(self, channel_id, user_id):
        with self.connection:
            name = self.cursor.execute('SELECT `name` FROM `channels` WHERE `channel_id` = ?', (channel_id,)).fetchall()
            all = self.cursor.execute("SELECT `channels` FROM `subscriptions` WHERE `user_id` = ?", (user_id,)).fetchall()
            a = all[0][0].split(', ')
            a.remove(name[0][0])
            result = ', '.join(a)
            self.cursor.execute("UPDATE `subscriptions` SET `channels` = ? WHERE `user_id` = ?", (result, user_id))
            return name[0][0]


    def update_channel(self, channel_id, video_count, subscribers):
        with self.connection:
            return self.cursor.execute("UPDATE `channels` SET `video_count` = ?, `subscribers` = ? WHERE `channel_id` = ?", (video_count, subscribers, channel_id))

    def get_user_channels(self, user_id):
        with self.connection:
            names = self.cursor.execute("SELECT `channels` FROM `subscriptions` WHERE `user_id` = ?", (user_id,)).fetchall()
            names = names[0][0].split(', ')
            array = []
            for name in names:
                id = self.cursor.execute("SELECT `channel_id` FROM `channels` WHERE `name` = ?", (name,)).fetchall()
                id = id[0][0]
                string = name + '\n' + '(' + id + ')'
                array.append(string)
            return array 
    
    def get_all_channels(self):
        with self.connection:
            return self.cursor.execute("SELECT `channel_id` FROM `channels`", ()).fetchall()

    def update_video_count(self, channel_id, video_count):
        with self.connection:
            return self.cursor.execute("UPDATE `channels` SET `video_count` = ? WHERE `channel_id` = ?", (video_count, channel_id))

    def get_video_count(self, channel_id):
        with self.connection:
            return self.cursor.execute("SELECT `video_count` FROM `channels` WHERE `channel_id` = ?", (channel_id,)).fetchall()[0][0]

    def increase_video_count(self, channel_id, video_count):
        with self.connection:
            return self.cursor.execute("UPDATE `channels` SET `video_count` = ? WHERE `channel_id` = ?", (video_count + 1, channel_id))

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()