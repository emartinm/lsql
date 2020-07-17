# Comandos importantes
```
# Calcular migraciones pendientes
$ python manage.py makemigrations

# Aplicar migracions pendientes
$ python manage.py migrate

# Copia los ficheros estáticos de todas las aplicacionies
# al directorio especificado en STATIC_ROOT
$ python manage.py collectstatic

# Lanzar el servidor
$ python manage.py runserver

# Abrir un shell y consultar/crear objetos
$ python manage.py shell
>>> from judge.models import SelectProblem
>>> SelectProblem.objects.all()
<QuerySet [<SelectProblem: hola>, <SelectProblem: hola>]>
>>> p = SelectProblem.objects.all()[0]
>>> Crear un nuevo objeto con los datos de p
>>> p.id = None
>>> p.pk = None
>>> p.save()
```
