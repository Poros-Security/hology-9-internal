cat > src/run.sh <<'EOF'
#!/bin/sh
exec socat tcp-l:11133,reuseaddr,fork exec:"python3 chall.py",stderr,pty
EOF
chmod +x src/run.sh
