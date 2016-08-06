set -x
sudo pip install --upgrade --user googleapiclient gviz-data-table
function copylib() {
  $(pip show $1  | egrep "^Location|^Requires" | awk -F ": " '{print "export "$1"="$2}' | sed -e "s/, /,/g")
  if [ -e $Location/$1 ]; then
    cp -R $Location/$1 $2
  else
    cp -R $Location/$(echo $1 | sed -e "s/-/_/g") $2
  fi;
  if [ $Requires ]; then
    echo $Requires | tr , "\n" | while read r; do
      copylib $r $2;
    done;
  fi;
}
copylib googleapiclient .
copylib gviz-data-table .
set +x
