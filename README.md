# Bot Reputación

Bot para llevar un ránking de la reputación de los usuarios en un canal de Telegram y otras tonterias ...

## General el Build

```
git clone https://github.com/Cebeerre/botreputacion.git
cd botreputacion
docker build -t botreputacion .
```

## Editar el archivo vars.env

Edita el archivo para configurar el Token del BOT generado por Botfather y los rangos/nombres de los níveles.

```
BOT_TOKEN=XXXXXXXXX:YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
BOT_RANKING_LVL_0=-100000,0,Nivel 0
BOT_RANKING_LVL_1=1,20,Nivel 1
BOT_RANKING_LVL_2=21,40,Nivel 2
BOT_RANKING_LVL_3=41,70,Nivel 3
BOT_RANKING_LVL_4=71,100,Nivel 4
BOT_RANKING_LVL_5=101,140,Nivel 5
BOT_RANKING_LVL_6=141,200,Nivel 6
BOT_RANKING_LVL_7=201,300,Nivel 7
BOT_RANKING_LVL_8=301,400,Nivel 8
BOT_RANKING_LVL_9=1000,100000,Nivel 9
```

## Arranca el Bot

```
docker run -d \
  --name=botreputacion \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Madrid \
  --env-file=./vars.env
  -v <path to data>:/app/data \
  --restart unless-stopped \
  botreputacion
```

Recuerda que debes añadir el bot al grupo y hacerlo admin del mismo para que pueda leer los mensajes de los usuarios. El bot empezará a funcionar automáticamente. Para ver los comandos disponibles ```/ayuda```

## Resetear la base de datos de palabras y el top cotorras diariamente

Añadir en el crontab del **host** un simple echo que vacíe los ficheros. Hay que cambiar el path en el **host** y el chat_id correspondiente del grupo:

```
0 5 * * * echo -n > <path to data>/database_words-123456789.json
0 5 * * * echo -n > <path to data>/database_noisy_users-123456789.json
```




