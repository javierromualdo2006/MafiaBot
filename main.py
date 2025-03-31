import discord
from discord.ext import commands
import random
import os
import asyncio
from dotenv import load_dotenv
from fase_noche import fase_noche

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de los intents
intents = discord.Intents.default()
intents.message_content = True  # Permitir acceso al contenido de los mensajes
intents.guilds = True
intents.dm_messages = True

# Crear y asignar un event loop antes de instanciar el bot
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Inicializar el bot (sin pasar el loop)
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario para las partidas
partidas = {}
roles = ["Mafioso", "Ciudadano", "Doctor", "Detective"]

@bot.command()
async def mafia(ctx, action: str, *args):
    guild_id = ctx.guild.id
    
    # Acción para crear una partida
    if action == "crear":
        if guild_id in partidas:
            await ctx.send("⚠️ Ya hay una partida en curso. ¡Espera a que termine o únete a ella!")
            return
        
        try:
            num_jugadores = int(args[0])
            if num_jugadores < 4:
                await ctx.send("❌ El mínimo de jugadores es 4. ¡Vamos a divertirnos con todos!")
                return
        except (IndexError, ValueError):
            await ctx.send("💡 Uso: `!mafia crear <número de jugadores>`")
            return
        
        partidas[guild_id] = {
            "jugadores": {},
            "max": num_jugadores,
            "iniciada": False,
            "fase": "noche",  # Empezamos en la fase de noche
            "eleccion_mafiosos": None
        }
        await ctx.send(f"🎲 ¡Se ha creado una partida de Mafia para {num_jugadores} jugadores! Usa `!mafia unirme` para participar. 🤝")
    
    # Acción para unirse a la partida
    elif action == "unirme":
        if guild_id not in partidas:
            await ctx.send("❌ No hay ninguna partida creada. Usa `!mafia crear <número de jugadores>` para empezar.")
            return
        
        partida = partidas[guild_id]
        if ctx.author in partida["jugadores"]:
            await ctx.send("🚫 Ya estás en la partida. ¡No puedes unirte dos veces!")
            return
        
        if len(partida["jugadores"]) >= partida["max"]:
            await ctx.send("⚡ La partida ya está llena. ¡Sigue esperando a la siguiente!")
            return
        
        partida["jugadores"][ctx.author] = None
        await ctx.send(f"{ctx.author.display_name} se ha unido. Jugadores actuales: {len(partida['jugadores'])}/{partida['max']} 🌟")
        
        if len(partida["jugadores"]) == partida["max"]:
            await iniciar_partida(ctx, guild_id)
    
    # Acción para iniciar la fase de noche manualmente
    elif action == "noche":
        if guild_id not in partidas:
            await ctx.send("❌ No hay ninguna partida activa. Usa `!mafia crear <número de jugadores>` para comenzar.")
            return
        await fase_noche(ctx, partidas[guild_id], guild_id)

    else:
        await ctx.send("❓ Comando inválido. Usa `!mafia crear <número de jugadores>` o `!mafia unirme`.")

# Función para iniciar la partida y cambiar automáticamente a la fase de noche
async def iniciar_partida(ctx, guild_id):
    partida = partidas[guild_id]
    jugadores = list(partida["jugadores"].keys())
    
    # Mezclar jugadores al azar
    random.shuffle(jugadores)
    
    num_jugadores = len(jugadores)
    num_mafiosos = max(1, num_jugadores // 4)  # Aproximadamente 25% de mafiosos
    
    # Asignar roles: mafiosos y ciudadanos
    roles_asignados = ["Mafioso"] * num_mafiosos + ["Ciudadano"] * (num_jugadores - num_mafiosos)
    random.shuffle(roles_asignados)
    
    # Asignar roles a cada jugador y enviarles un mensaje privado
    for i, jugador in enumerate(jugadores):
        partida["jugadores"][jugador] = roles_asignados[i]
        try:
            await jugador.send(f"🔐 **Tu rol es**: **{roles_asignados[i]}**.")
        except discord.Forbidden:
            await ctx.send(f"⚠️ No puedo enviar mensaje privado a {jugador.display_name}. Asegúrate de tener los DMs habilitados.")
    
    # Guardar la lista de mafiosos en la partida
    mafiosos = [jugadores[i] for i, rol in enumerate(roles_asignados) if rol == "Mafioso"]
    partida["roles"] = {"mafiosos": mafiosos}
    
    print(f"Roles asignados: {partida['roles']}")
    
    await ctx.send("🎉 ¡La partida ha comenzado! Los roles han sido asignados en privado. 🌟")
    partida["iniciada"] = True
    partida["fase"] = "noche"
    await ctx.send("🌙 La fase de noche ha comenzado. Los mafiosos pueden hacer su elección. 🔪")
    await fase_noche(ctx, partida, guild_id)

# Iniciar el bot
bot.run(os.getenv("DISCORD_TOKEN"))
