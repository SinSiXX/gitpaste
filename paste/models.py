import os
import logging
from paste.ext.git import Git

from collections import defaultdict

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

logger = logging.getLogger(__name__)

_paste_memoize = defaultdict(lambda: list)


def clear_paste_memoization(pk):
    try:
        global _paste_memoize
        del _paste_memoize[pk]
    except KeyError:
        pass


def add_paste_memoization(pk, data):
    global _paste_memoize
    _paste_memoize[pk] = data
    return data


def get_paste_memoization(pk):
    return _paste_memoize[pk]


class Paste(models.Model):
    """A paste is a collection of files. It also acts as metadata for the
    files under the collection. A paste itself can be forked and marked as
    private.

    """
    owner = models.ForeignKey(
        User, null=True, blank=True,
        help_text=_("The owner of the paste. A null user implies an "
                    "anonymous user."))

    description = models.CharField(
        max_length=120, blank=True,
        help_text=_("A summary or quick detail of this paste."))

    repository = models.FilePathField(
        path=settings.GITPASTE_REPOSITORY, allow_files=False,
        allow_folders=True, help_text=_("The location of the Git repository"))

    private = models.BooleanField(
        default=False,
        help_text=_("If enabled, then this paste will only be accessible by "
                    "the original user or by a special URL."))

    private_key = models.CharField(
        max_length=5, blank=False,
        help_text=_("A small 5-character hash for private URL access"))

    views = models.IntegerField(help_text=_("The number of views"))
    created = models.DateTimeField(auto_now_add=True)
    fork = models.ForeignKey("Paste", null=True, blank=True)

    def save(self, *args, **kwargs):
        """save -> Paste
        Saves the Paste object and creates the new repository.

        """
        if self.pk is None:
            import uuid
            user = self.owner or "anonymous"
            folder = slugify(self.description)[:10] + '-' + str(uuid.uuid4())
            path = os.sep.join([settings.GITPASTE_REPOSITORY, user, folder])
            self.repository = path
            os.makedirs(path, mode=0o777, exist_ok=True)
            git = Git(self.repository)
            git.init()
        return super(Paste, self).save(*args, **kwargs)

    def add_file(self, filename, content):
        """add_file -> None
        Adds a file to the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist

        path = os.sep.join([self.repository, filename])

        commit_message = "Adds {0}".format(filename)
        if os.path.exists(path):
            commit_message = "Updates {0}".format(filename)

        with open(path, "w") as f:
            f.write(content)

        git = Git(self.repository)
        git.add(path)
        git.commit(commit_message)

    def delete_file(self, filename):
        """delete_files -> None
        Deletes a file from the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist
        commit_message = "Removes {0}".format(filename)
        path = os.sep.join([self.repository, filename])
        git = Git(self.repository)
        git.rm(path)
        git.commit(commit_message)

    @property
    def status(self):
        """status -> string
        Retrieves the status of the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist
        git = Git(self.repository)
        return git.status()

    @property
    def log(self):
        """status -> string
        Retrieves the status of the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist
        git = Git(self.repository)
        return git.log()

    @property
    def files(self):
        """files -> [(filename, path, content), ...]
        Returns the files associated with the repository.

        """
        if self.pk is None:
            raise Paste.DoesNotExist

        memoized = get_paste_memoization(self.pk)
        if memoized:
            return memoized

        files = [f for f in os.listdir(self.repository) if '.git' not in f]
        data = []
        for filename in files:
            path = os.sep.join([self.repository, filename])
            content = open(path).read()
            data.append((filename, path, content))

        return add_paste_memoization(self.pk, data)