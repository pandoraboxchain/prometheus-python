echo "Converting dot files to images";
for f in *.dot
do
    dot -Tpng $f -o $f.png
done
