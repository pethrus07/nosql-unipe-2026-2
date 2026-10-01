// Atividade 1 - Etapa 2 - Inserindo um documento na colecao restaurants

var resultado = db.restaurants.insertOne( {
   "address" : {
      "street" : "2 Avenue",
      "zipcode" : "10075",
      "building" : "1480",
      "coord" : [ -73.9557413, 40.7720266 ]
   },
   "borough" : "Manhattan",
   "cuisine" : "Italian",
   "grades" : [
      { "date" : ISODate("2014-10-01T00:00:00Z"), "grade" : "A", "score" : 11 },
      { "date" : ISODate("2014-01-16T00:00:00Z"), "grade" : "B", "score" : 17 }
   ],
   "name" : "Vella",
   "restaurant_id" : "41704620"
} )

printjson( resultado )
