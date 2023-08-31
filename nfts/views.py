from django.http import JsonResponse
from rest_framework import generics, status
from django.utils import timezone
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, HttpResponse, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


class NFTListView(generics.ListAPIView):
    queryset = NFT.objects.order_by('-addTime')
    serializer_class = NFTSerializer


class StartAuctionView(APIView):
    def put(self, request, nft_id):
        try:
            nft = NFT.objects.get(pk=nft_id)
            serializer = StartAuctionSerializer(
                nft, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(is_auction=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except NFT.DoesNotExist:
            return Response({"message": "NFT not found."}, status=status.HTTP_404_NOT_FOUND)


class PlaceBidView(APIView):
    def post(self, request, nft_id):
        try:
            nft = NFT.objects.get(pk=nft_id)
            current_time = timezone.now()
            if nft.auction_start_time <= current_time <= nft.auction_end_time:
                highest_bid = request.data.get('highest_bid')
                highest_bidder = request.user
                if highest_bid is not None and highest_bid > nft.highest_bid:
                    nft.highest_bid = highest_bid
                    nft.highest_bidder = highest_bidder
                    nft.save()
                    serializer = NFTBidSerializer(nft)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Bid should be higher than the current highest bid."},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"message": "Auction is not currently active."},
                                status=status.HTTP_400_BAD_REQUEST)
        except NFT.DoesNotExist:
            return Response({"message": "NFT not found."}, status=status.HTTP_404_NOT_FOUND)


class EndAuctionView(APIView):
    def post(self, request, nft_id):
        try:
            nft = NFT.objects.get(pk=nft_id)
            current_time = timezone.now()
            if nft.auction_end_time < current_time and nft.is_auction:
                highest_bid = nft.highest_bid
                highest_bidder = nft.highest_bidder
                if highest_bidder:
                    nft.sold = True
                    nft.is_auction = False
                    nft.save()
                    serializer = NFTBidSerializer(nft)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "No bids were made for this NFT."},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"message": "Auction is still active."},
                                status=status.HTTP_400_BAD_REQUEST)
        except NFT.DoesNotExist:
            return Response({"message": "NFT not found."}, status=status.HTTP_404_NOT_FOUND)


from rest_framework import permissions

class CartItemView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        nft_id = request.data.get("nft_id")
        quantity = request.data.get("quantity", 1)

        try:
            nft = NFT.objects.get(pk=nft_id)
        except NFT.DoesNotExist:
            return Response({"message": "NFT not found."}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user, nft=nft)
        cart_item.quantity += quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, nft_id):
        try:
            cart_item = CartItem.objects.get(user=request.user, nft__id=nft_id)
            cart_item.delete()
            return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"message": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)


class FavoritesView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            favorite_nfts = Favorite.objects.filter(user=request.user).values(
                'nft__id', 'nft__name', 'nft__image', 'nft__price', 'nft__highest_bid', 'nft__addTime')
            return JsonResponse({"favorites": list(favorite_nfts)})
        else:
            return JsonResponse({'message': 'User not authenticated.'}, status=401)

    def post(self, request):
        nft_id = request.data.get("nft")

        if not nft_id or not request.user:
            return Response({"message": "NFT or user not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            nft = NFT.objects.get(id=nft_id)
        except:
            return Response({"message": "NFT not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            fv=Favorite.objects.get(user=request.user, nft=nft)
            fv.delete()
            return Response( status=status.HTTP_204_NO_CONTENT)
        except Exception:
            favorite = Favorite.objects.create(user=request.user, nft=nft)
            serializer = FavoriteSerializer(favorite)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmailAPI(APIView):
    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        message = request.data.get('message')

        if name is None and email is None and message is None:
            return Response({'message': 'There must be a name, email or message'}, status=400)
        elif email is None:
            return Response({'message': 'Email is required.'}, status=400)
        elif message is None:
            return Response({'message': 'Message is required.'}, status=400)
        else:
            Contact.objects.create(name=name, email=email, message=message)

            send_mail(
                subject=f"Contact Email from {name} - email : {email}",
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )

        return Response("Success", status=status.HTTP_200_OK)
        
        
    
          

"""def Message(request):

    return render(request, "Messagesent.jsx")
"""
   