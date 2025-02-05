def user_info(request):
    username = None
    user_image = None
    if request.user.is_authenticated:
        user_image = request.user.image.url
        username = request.user.username

    return {'username': username , 'user_image' : user_image}

