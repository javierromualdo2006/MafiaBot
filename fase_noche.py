import discord
import asyncio

async def fase_noche(ctx, partida, guild_id):
    mafiosos = partida["roles"]["mafiosos"]
    partida["fase"] = "noche"
    partida["objetivo"] = None

    # Crear o buscar la categoría "Partidas Mafia"
    categoria = discord.utils.get(ctx.guild.categories, name="Partidas Mafia")
    if not categoria:
        categoria = await ctx.guild.create_category("Partidas Mafia")

    # Definir los permisos para el canal privado
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }
    for mafioso in mafiosos:
        overwrites[mafioso] = discord.PermissionOverwrite(read_messages=True)
    canal_privado = await ctx.guild.create_text_channel("decisiones-mafia", category=categoria, overwrites=overwrites)

    await ctx.send("🌙 **La noche ha caído.**\nLos mafiosos deben decidir a quién eliminar en secreto.")

    # Preparar la lista de jugadores disponibles (excluyendo a los mafiosos)
    lista_jugadores = "\n".join(
        [f"- {jugador.mention}" for jugador in partida["jugadores"].keys() if jugador not in mafiosos]
    )

    # Enviar el mensaje de instrucciones al canal privado de los mafiosos
    await canal_privado.send(
        "🔒 **🌙 Fase de Noche**\n"
        "🤫 *Eres un mafioso. Selecciona a tu objetivo respondiendo con su nombre o mención.*\n"
        "📜 Lista de jugadores disponibles:\n"
        f"{lista_jugadores}\n\n"
        "✍️ **Responde con el nombre o mención del jugador que deseas eliminar.**\n"
        "📝 **Si deseas no matar a nadie esta noche, responde con `skip`.**"
    )

    # Función de verificación para la respuesta
    def check_respuesta(message):
        return message.author in mafiosos and message.channel == canal_privado

    # Espera indefinidamente la respuesta de algún mafioso
    respuesta = await ctx.bot.wait_for("message", check=check_respuesta)
    contenido = respuesta.content.lower()

    if contenido == "skip":
        partida["objetivo"] = None
        await canal_privado.send("🔕 Los mafiosos han decidido no matar a nadie esta noche. 😇")
    else:
        objetivo = None
        # Iterar sobre los jugadores para encontrar aquel que coincida con la respuesta
        for jugador in partida["jugadores"].keys():
            if contenido == jugador.display_name.lower() or contenido == jugador.mention:
                objetivo = jugador
                break

        if objetivo:
            partida["objetivo"] = objetivo
            await canal_privado.send(
                f"✅ **Se ha seleccionado a {objetivo.display_name} como objetivo.**\n"
                "🕰️ Se procesará al amanecer."
            )
        else:
            await canal_privado.send("❌ No se pudo identificar al jugador. Intenta nuevamente en la próxima noche.")

    # Eliminar el canal privado de la fase de noche
    await canal_privado.delete()

    # Procesar el resultado en la fase de amanecer
    await amanecer(ctx, partida, guild_id)

async def amanecer(ctx, partida, guild_id):
    objetivo = partida.get("objetivo", None)
    partida["fase"] = "día"

    if objetivo:
        if objetivo in partida["jugadores"]:
            del partida["jugadores"][objetivo]
        await ctx.send(
            f"🌅 **El amanecer ha llegado.**\n"
            f"💀 Anoche, {objetivo.mention} fue asesinado por la mafia. 😵"
        )
    else:
        await ctx.send("🌅 **El amanecer ha llegado.**\n😇 Nadie murió anoche.")
