from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Client, Project
from .serializers import ClientSerializer, ProjectSerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def create(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        client = self.get_object()
        client.client_name = request.data.get('client_name', client.client_name)
        client.updated_at = timezone.now()
        client.save()
        return Response(ClientSerializer(client).data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        client = self.get_object()
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# class ProjectViewSet(viewsets.ModelViewSet):
#     queryset = Project.objects.all()
#     serializer_class = ProjectSerializer

#     def create(self, request, client_id=None):
#         client = get_object_or_404(Client, id=client_id)
#         project_name = request.data.get('project_name')
#         users_data = request.data.get('users')
#         users = [get_object_or_404(User, id=user['id']) for user in users_data]

#         project = Project.objects.create(
#             project_name=project_name,
#             client=client,
#             created_by=request.user
#         )
#         project.users.set(users)
#         project.save()

#         return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def create(self, request, client_id=None):
        # Validate the presence of required fields
        project_name = request.data.get('project_name')
        users_data = request.data.get('users')

        # Check if project_name or users data is missing
        if not project_name:
            return Response({"error": "Project name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not users_data:
            return Response({"error": "Users list is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the client based on the client_id in the URL
        client = get_object_or_404(Client, id=client_id)

        # Retrieve users and handle any invalid user IDs
        try:
            users = [get_object_or_404(User, id=user['id']) for user in users_data]
        except KeyError:
            return Response({"error": "Invalid user data format"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the project and assign it to the client and users
        project = Project.objects.create(
            project_name=project_name,
            client=client,
            created_by=request.user
        )
        project.users.set(users)
        project.save()

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def user_projects(self, request):
        projects = request.user.projects.all()
        return Response(ProjectSerializer(projects, many=True).data, status=status.HTTP_200_OK)