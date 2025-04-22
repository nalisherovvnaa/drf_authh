from rest_framework.response import Response
from .models import Car
from .serializers import CarSerializer
from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication

# Create your views here.

class CarsListView(generics.GenericAPIView):
    # permission_classes = permissions.IsAuthenticated,
    authentication_classes = TokenAuthentication,

    def get(self, request, *args, **kwargs):
        cars = Car.objects.all()
        serializer = CarSerializer(cars, many=True)
        return Response({
            'data': serializer.data,
            'status': status.HTTP_200_OK,
            'message': 'Cars List' if serializer.data else 'No data yet',
        })


class CarCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CarSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                'data': serializer.data,
                'status': status.HTTP_201_CREATED,
                'message': 'Book Created'
            }

        else:
            response = {
                'data': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Invalid data'
            }

        return Response(response)
    

class CarUpdateView(APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request, pk):
        try:
            car = Car.objects.get(id=pk)
            serializer = CarSerializer(car, data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {
                    'data': serializer.data,
                    'status': status.HTTP_200_OK,
                    'message': 'Book Updated'
                }
            else:
                response = {
                    'data': serializer.errors,
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Invalid data'
                }
            return Response(response)
        
        except Exception as e:
            response = {
                'data': str(e),
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Car not found'
            }
            return Response(response)

    def patch(self, request, pk):
        try:
            car = Car.objects.get(id=pk)
            serializer = CarSerializer(car, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response = {
                    'data': serializer.data,
                    'status': status.HTTP_200_OK,
                    'messages': 'Book Updated'
                }
            else:
                response = {
                    'data': serializer.errors,
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Invalid data'
                }
            return Response(response)
        
        except Exception as e:
            response = {
                'data': str(e),
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Car not found'
            }
            return Response(response)


class CarDetailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, pk):
        try:
            car = Car.objects.get(id=pk)
            serializer = CarSerializer(car)
            response = {
                'data': serializer.data,
                'status': status.HTTP_200_OK,
                'message': 'Car data'
            }
            return Response(response)
        
        except Exception as message:
                response = {
                    'data': str(message),
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'Car not found'
                }
                return Response(response)


class CarDeleteView(APIView):
    permission_classes = (permissions.AllowAny,)

    def delete(self, request, pk):
        try:
            car = Car.objects.get(id=pk)
            car.delete()
            response = {
                'data': None,
                'status': status.HTTP_200_OK,
                'message': 'Car deleted'
            }
            return Response(response)

        except Exception as message:
            response = {
                'data': str(message),
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Car not found'
            }
            return Response(response)
    

# Viewsets orqali yozilgan view
class CarsViewSets(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer