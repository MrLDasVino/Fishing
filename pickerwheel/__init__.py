from .pickerwheel import PickerWheel

async def setup(bot):
    
    bot.add_cog(PickerWheel(bot))

