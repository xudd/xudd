(import [xudd.actor [Actor]])
(import [xudd.hive [Hive]])
(import [xudd.demos.server [Server]])

(defmacro actor-instance [hive class id]
  "Create a new actor instance attached to a hive.
  Returns the id of the created actor"
  (quasiquote
    (do
      (print
        (.format "creating new actor: {0} {1} {2}"
          (unquote hive)
          (unquote class)
          (unquote id)))
      (kwapply (.create-actor (unquote hive) (unquote class))
        {"id" (unquote id)}))))

(defn main []
  (setv hive (Hive))
  (kwapply (.send-message hive)
    {"to" (actor-instance hive Server "server")
     "directive" "listen"})
  (.run hive))

(if (= --name-- "__main__")
  (do
    (main)))
