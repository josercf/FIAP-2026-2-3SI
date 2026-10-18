# Serviço de Faturamento (C#, .NET 8). Multi-stage: o SDK, que passa de
# 700 MB, só existe no estágio de compilação; a imagem final leva o runtime
# ASP.NET Core e os assemblies publicados.

FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS build
WORKDIR /build
COPY Faturamento.csproj .
RUN dotnet restore
COPY Program.cs .
RUN dotnet publish -c Release -o /publicado --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=build /publicado .

ENV DOTNET_EnableDiagnostics=0 \
    ASPNETCORE_ENVIRONMENT=Production

USER logitech
EXPOSE 5080
CMD ["dotnet", "Faturamento.dll"]
