# gopy

This is a simple web-app for creating user friendly URL links.

The idea is to map a user un-friendly link to a more user friendly
one.  These links are configured by editing a text file.

For example, you could have a configuration item:

```
google https://google.com/ Search engine
```

Then on your web browser address bar you would enter one of these:

- `go.example.com/google`
- `go.example.com/go`
- `go.example.com/search`

The first example, it would be a direct match.  The second and
third example would match the substring.

If there are multiple matches, a list of matching results will
be shown.

If you go to that page without any queries as in:

- `go.example.com`

Then it would list all the *public* routes.  That way you
could have routes that are only accessible if the user
knows how to search for it.


