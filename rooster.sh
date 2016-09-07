until python rooster.py do;
    echo "Rooster crashed with exit code $?... Respawning" >&2
    sleep 2
done