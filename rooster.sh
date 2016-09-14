until python rooster.py; do
    echo "Rooster crashed with exit code" >&2
    echo $? >&2
    echo "... Respawning" >&2
    sleep 2;
done
