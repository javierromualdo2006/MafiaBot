import discord
from discord.ext import commands
import random
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de los intents
intents = discord.Intents.default()
intents.message_content = True  # Permitir acceso al contenido de los mensajes
intents.guilds = True
intents.dm_messages = True

# Inicializar el bot con los intents configurados
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario para las partidas
partidas = {}
roles = ["Mafioso", "Ciudadano", "Doctor", "Detective"]

@bot.command()
async def mafia(ctx, action: str, *args):
    print(f"Comando recibido: !mafia {action}")  # Depuración
    guild_id = ctx.guild.id
    
    # Acción para crear una partida
    if action == "crear":
        if guild_id in partidas:
            await ctx.send("Ya hay una partida en curso.")
            return
        
        try:
            num_jugadores = int(args[0])
            if num_jugadores < 4:
                await ctx.send("El mínimo de jugadores es 4.")
                return
        except (IndexError, ValueError):
            await ctx.send("Uso: !mafia crear <número de jugadores>")
            return
        
        partidas[guild_id] = {
            "jugadores": {},
            "max": num_jugadores,
            "iniciada": False
        }
        await ctx.send(f"Se ha creado una partida de Mafia para {num_jugadores} jugadores. Usa `!mafia unirme` para participar.")
    
    # Acción para unirse a la partida
    elif action == "unirme":
        if guild_id not in partidas:
            await ctx.send("No hay ninguna partida creada. Usa `!mafia crear <número de jugadores>` para empezar.")
            return
        
        partida = partidas[guild_id]
        if ctx.author in partida["jugadores"]:
            await ctx.send("Ya estás en la partida.")
            return
        
        if len(partida["jugadores"]) >= partida["max"]:
            await ctx.send("La partida ya está llena.")
            return
        
        partida["jugadores"][ctx.author] = None
        await ctx.send(f"{ctx.author.display_name} se ha unido. Jugadores actuales: {len(partida['jugadores'])}/{partida['max']}")
        
        if len(partida["jugadores"]) == partida["max"]:
            await iniciar_partida(ctx, guild_id)
    else:
        await ctx.send("Comando inválido. Usa `!mafia crear <número de jugadores>` o `!mafia unirme`.")

async def iniciar_partida(ctx, guild_id):
    partida = partidas[guild_id]
    jugadores = list(partida["jugadores"].keys())
    random.shuffle(jugadores)
    
    asignacion_roles = random.choices(roles, k=len(jugadores))
    for i, jugador in enumerate(jugadores):
        partida["jugadores"][jugador] = asignacion_roles[i]
        try:
            await jugador.send(f"Tu rol es **{asignacion_roles[i]}**.")
        except discord.Forbidden:
            await ctx.send(f"No puedo enviar mensaje privado a {jugador.display_name}. Asegúrate de tener los DMs habilitados.")
    
    await ctx.send("La partida ha comenzado. Los roles han sido asignados en privado.")
    partida["iniciada"] = True

# Obtener el token desde las variables de entorno
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise ValueError("No se encontró el token de Discord. Asegúrate de que está en tu archivo .env con la clave DISCORD_TOKEN.")

# Iniciar el bot
bot.run(TOKEN)
