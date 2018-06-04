#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>

#define T_TABLA_CONTX 100
#define T_CONTX 100
#define T_LINEA 10000


#define SEPARADOR '{'
#define ORDEN_BORRAR 'd'
#define ORDEN_CREAR 'c'

#define RUTA_DIRECTORIO_IN "/var/log/elkorrelator/in/"
#define RUTA_FICHERO_TMP "/var/log/elkorrelator/tmp/fichero"
#define RUTA_FICHERO_OUT "/var/log/elkorrelator/out/orquestador.log"
#define RUTA_FICHERO_TOUCH "/var/log/elkorrelator/in/touch"
#define BANNER "\nELKorrelator\n\n"

#define T_COMANDO_FICHERO 300
#define T_COMANDO_CORRELADOR 600
#define T_NOMBRE_FICHERO_IN 100

#define COMANDO_FICHERO_1 "ls -t "
#define COMANDO_FICHERO_2 "|head -1 | sed \'s;^;"
#define COMANDO_FICHERO_3 ";\' > "

#define COMANDO_CORRELADOR_1 "python /usr/share/elkorrelator/bin/correlador.py \'\""
#define COMANDO_CORRELADOR_2 "\"\' & "

#define CARACTERES_VALIDOS "0123456789abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZ .:,;_\"\n()[]{}@#$%/=+*-"

//0->DEBUG
//1->INFO
//2->ERROR
#define NIVEL_DEBUG 1


static const int nivel_debug = NIVEL_DEBUG;
// Puntero del fichero de log
FILE *fichero_log;


//Basado en https://svn.apache.org/repos/asf/apr/apr/trunk/encoding/apr_base64.c
/* Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
static const char basis_64[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
int apr_base64_encode_len(int len){
    return ((len + 2) / 3 * 4) + 1;
}


int apr_base64_encode(char *encoded, const char *string, int len)
{
    int i;
    char *p;

    p = encoded;
    for (i = 0; i < len - 2; i += 3) {
	*p++ = basis_64[(string[i] >> 2) & 0x3F];
	*p++ = basis_64[((string[i] & 0x3) << 4) |
	                ((int) (string[i + 1] & 0xF0) >> 4)];
	*p++ = basis_64[((string[i + 1] & 0xF) << 2) |
	                ((int) (string[i + 2] & 0xC0) >> 6)];
	*p++ = basis_64[string[i + 2] & 0x3F];
    }
    if (i < len) {
	*p++ = basis_64[(string[i] >> 2) & 0x3F];
	if (i == (len - 1)) {
	    *p++ = basis_64[((string[i] & 0x3) << 4)];
	    *p++ = '=';
	}
	else {
	    *p++ = basis_64[((string[i] & 0x3) << 4) |
	                    ((int) (string[i + 1] & 0xF0) >> 4)];
	    *p++ = basis_64[((string[i + 1] & 0xF) << 2)];
	}
	*p++ = '=';
    }

    *p++ = '\0';
    return p - encoded;
}
//FIN Basado en https://svn.apache.org/repos/asf/apr/apr/trunk/encoding/apr_base64.c

// Esta funcion se encarga de comprobar si un caracter esta en la lista de caracteres validos para evitar posibles inyecciones
short caracterValido(char caracter){
    char validos[] = CARACTERES_VALIDOS;
    char * pch;
    pch=strchr(validos,caracter);
    if (pch!=NULL){
        return 1;
    }
    return 0;
}

//Esta funcion crea un nuevo contexto
//Devuelve 1 si lo puede crear
short crearContexto(char *tabla, char* contx, long t_contexto, long t_tabla_contextos, long posicion){
    for (unsigned long i=posicion; i < t_tabla_contextos; i++){
        if ((tabla+i*t_contexto)[0]=='\0'){
            strcpy((tabla+i*t_contexto),contx);
            return 1;
        }
    }
    return 0;
}

//Esta funcion elimina un contexto existente
//Devuelve 1 si lo puede borrar
short borrarContexto(char *tabla, char* contx, long t_contexto, long t_tabla_contextos){
    for (unsigned long i = 0; i < t_tabla_contextos; i++){
        if ((tabla+i*t_contexto)[0]=='\0'){
            return 0;
        }
        if (strcmp((tabla+i*t_contexto),contx) == 0){
            (tabla+i*t_contexto)[0]='\0';
            for(;i < t_tabla_contextos-1; i++){
                strcpy((tabla+i*t_contexto),(tabla+(i+1)*t_contexto));
            }
            return 1;
        }
    }
    return 0;
}

//Esta funcion comprueba si un contexto ya existe
//Si existe devuelve -1
//Si no existe devuelve la primera posicion vacia
unsigned long existeContexto(char *tabla, char* contx, long t_contexto, long t_tabla_contextos, unsigned short* existe){
    if(nivel_debug<=0){
        for (unsigned long i = 0; i < t_tabla_contextos; i++){
				fichero_log = fopen(RUTA_FICHERO_OUT, "a");
				fprintf(fichero_log,"[DEBUG] tabla[%lu]: %s\n",i,(tabla+i*t_contexto));
				fclose(fichero_log);
        }
    }
    unsigned long i;
    for (i = 0; i < t_tabla_contextos; i++){
        //array tabla (tabla+i*t_contexto)
        if ((tabla+i*t_contexto)[0]=='\0'){
            *existe=0;
            return i;
        }
        if (strcmp((tabla+i*t_contexto),contx) == 0){
            *existe=1;
            return 0;
        }
    }
    //si llega hasta aqui no hay coincidencias
    *existe=0;
    return i;
}

// Obtiene el ultimo fichero modificado por el detector
void get_ultimo_modificado(char* buffer){
    //Vacio el string
    for(int i=0;i<T_NOMBRE_FICHERO_IN;i++){
        buffer[i]='\0';
    }

    //Se actualiza cual es el ultimo fichero modificado
    char comando[T_COMANDO_FICHERO];
    comando[0]='\0';
    strcat(comando,COMANDO_FICHERO_1);
    strcat(comando,RUTA_DIRECTORIO_IN);
    strcat(comando,COMANDO_FICHERO_2);
    strcat(comando,RUTA_DIRECTORIO_IN);
    strcat(comando,COMANDO_FICHERO_3);
    strcat(comando,RUTA_FICHERO_TMP);
    int systemRet=system(comando);
    if(systemRet == -1){
        if(nivel_debug<=2){
			fichero_log = fopen(RUTA_FICHERO_OUT, "a");
            fprintf(fichero_log,"[ERROR] Error al ejecutar el comando para obtener el ultimo fichero modificado\n");
			fclose(fichero_log);
        }
    }

    //Se obtiene la salida del comando anterior
    FILE *archivo;
	char caracter;

    archivo = fopen(RUTA_FICHERO_TMP,"r");
    int i=0;

    if (archivo == NULL){
      if(nivel_debug<=2){
        fichero_log = fopen(RUTA_FICHERO_OUT, "a");
        fprintf(fichero_log,"[ERROR] Error de apertura del archivo temporal. \n\n");
        fclose(fichero_log);
      }
    }
    else{
        while((caracter = fgetc(archivo)) != EOF){
            if(caracter=='\n'){
                break;
            }
            buffer[i]=caracter;
            i++;
            if(i==T_NOMBRE_FICHERO_IN-2){
                break;
            }
	    }
        fclose(archivo);
    }

}

int main(void)
{
    FILE *archivo;
    char caracter;

    FILE *fichero_touch;
    fichero_touch= fopen(RUTA_FICHERO_TOUCH,"w+");
    fprintf(fichero_touch,"\n");
    fclose(fichero_touch);

	//Esta variable servira para controlar si se quiere introducir o borrar un contexto
    char orden;

    //Sirve para diferenciar el contexto del log
    char separador=SEPARADOR;
    char orden_borrar=ORDEN_BORRAR;
    char orden_crear=ORDEN_CREAR;
    unsigned long tamano_contexto=T_CONTX;
    unsigned long tamano_tabla_contextos=T_TABLA_CONTX;

    char contexto[tamano_contexto];

    //Defino un string para almacenar el log


    unsigned long t_linea=T_LINEA;
    unsigned long indice_linea=0;
    char linea[t_linea];

    unsigned long t_linea_64=apr_base64_encode_len(t_linea);
    char linea_64[t_linea_64];
    for(int i=0;i<t_linea_64;i++){
        linea_64[i]='\0';
    }


    unsigned long indice_contexto=0;

    //Tabla de contextos
    char tabla_contextos[tamano_tabla_contextos][tamano_contexto];

    for(indice_contexto=0;indice_contexto<tamano_contexto;indice_contexto++){
        contexto[indice_contexto]='\0';
    }
    for(unsigned long i=0;i<t_linea;i++){
        linea[i]='\0';
    }
    for(unsigned long i=0;i<tamano_tabla_contextos;i++){
        for(indice_contexto=0;indice_contexto<tamano_contexto;indice_contexto++){
            tabla_contextos[i][indice_contexto]='\0';
        }
    }

    unsigned long t_comando_correlador=t_linea_64+T_COMANDO_CORRELADOR;

    char comando_init_correlar[t_comando_correlador];


    indice_contexto=0;

    char fichero_in[T_NOMBRE_FICHERO_IN];
    get_ultimo_modificado(fichero_in);

    if(nivel_debug<=1){
        fichero_log = fopen(RUTA_FICHERO_OUT, "a");
        fprintf(fichero_log,"[INFO] El fichero a leer es: %s\n",fichero_in);
        fclose(fichero_log);
    }
	archivo = fopen(fichero_in,"r");
    //archivo = fopen("prueba.txt","r");

    if (archivo == NULL){
        if(nivel_debug<=2){
			fichero_log = fopen(RUTA_FICHERO_OUT, "a");
            fprintf(fichero_log,"[ERROR] Error de apertura del archivo. \n\n");
			fclose(fichero_log);
        }
    }

    // Aqui comienza a trabajar el orquestador
    else{
        //time_t now = time(NULL);
	fichero_log = fopen(RUTA_FICHERO_OUT, "a");
        //fprintf(fichero_log,"[%s] %s", ctime(&now),BANNER);
        fprintf(fichero_log,"%s",BANNER);
	fclose(fichero_log);
        indice_linea=0;
        while(1){
            caracter = fgetc(archivo);
            // Se lee hasta el final de la linea o del archivo
            if(caracter!='\n' && caracter!=EOF){
                if(indice_linea<=t_linea-1){
                    if (caracterValido(caracter)){
                        linea[indice_linea]=caracter;
                    }else{
                        linea[indice_linea]='_';
                    }
                }
                indice_linea++;
            }
            // Cuando ya se ha leido la linea se evalua
            else{
            //si es el fin de la linea
                if(indice_linea!=0){
                //si la linea no esta vacia
                    orden=linea[0];
                    linea[indice_linea]='\0';
                    if(nivel_debug<=0){
			fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                        fprintf(fichero_log,"[DEBUG] indice_linea: %lu\n",indice_linea);
                        fprintf(fichero_log,"[DEBUG] LINEA: %s\n",linea);
                        fprintf(fichero_log,"[DEBUG] ORDEN: %c\n",orden);
			fclose(fichero_log);
                    }
                    indice_linea=0;
                    for(indice_contexto=0;indice_contexto<tamano_contexto-1;indice_contexto++){
                        if(linea[indice_contexto+1]==separador){
                            contexto[indice_contexto]='\0';
                            break;
                        }
                        contexto[indice_contexto]=linea[indice_contexto+1];
                    }
                    if(nivel_debug<=0){
			fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                        fprintf(fichero_log,"[DEBUG] CONTEXTO: %s\n",contexto);
			fclose(fichero_log);
                    }
                    if(orden==orden_crear||orden==orden_borrar){
                        // Si la orden es crear....
                        if(orden==orden_crear){
                            unsigned long posicion;
                            unsigned short v_existe=0;
                            unsigned short * existe=&v_existe;
                            posicion=existeContexto((char *)tabla_contextos,contexto,tamano_contexto,tamano_tabla_contextos,existe);
                            // Si el contexto no existe entonces se crea
                            if(!v_existe){
                                if(!crearContexto((char *)tabla_contextos,contexto,tamano_contexto,tamano_tabla_contextos,posicion)){
                                    if(nivel_debug<=2){
					fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                        fprintf(fichero_log,"[ERROR] No hay espacio para crear el contexto %s, espacio disponible %lu\n",contexto,tamano_tabla_contextos);
					fclose(fichero_log);
                                    }
                                }
                                else{
                                    if(nivel_debug<=1){
					fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                        fprintf(fichero_log,"[INFO] Se crea el contexto %s\n",contexto);
					fclose(fichero_log);
                                    }
                                    comando_init_correlar[0]='\0';

                                    //Obtener mensaje en base64

                                    for(unsigned long i=0;i<t_linea_64;i++){
                                        linea_64[i]='\0';
                                    }

                                    // Una vez creado el contexto se codifican os datos en bse64 y se le pasan a un correlador que se creara para que verifique si se cumple el caso de uso definido
                                    int ae=apr_base64_encode(linea_64,linea, t_linea);
                                    if(nivel_debug<=0){
					fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                        fprintf(fichero_log,"[DEBUG] Base64: %s\n",linea_64);
                                        fprintf(fichero_log,"[DEBUG] ");
                                        for(unsigned long i=0;i<t_linea_64;i++){
                                            fprintf(fichero_log,"%c",linea_64[i]);
                                        }
                                        fprintf(fichero_log,"\n");
                                        fprintf(fichero_log,"[DEBUG] EnteroBase64: %i\n",ae);
                                        fprintf(fichero_log,"[DEBUG] TamBase64: %lu\n",t_linea_64);
					fclose(fichero_log);
                                    }
                                    if(t_linea_64!=ae){
                                        if(nivel_debug<=2){
                                            fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                            fprintf(fichero_log,"[ERROR] La codificacion base64 ha fallado\n");
                                            fclose(fichero_log);
                                        }
                                    }
                                    strcat(comando_init_correlar,COMANDO_CORRELADOR_1);
                                    strcat(comando_init_correlar,linea_64);
                                    strcat(comando_init_correlar,COMANDO_CORRELADOR_2);
                                    int systemRet=system(comando_init_correlar);
                                    if(systemRet == -1){
                                        if(nivel_debug<=2){
                                            fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                            fprintf(fichero_log,"[ERROR] Error al ejecutar el comando para correlar\n");
                                            fclose(fichero_log);
                                        }
                                    }

                                }
                            }
                            else{
                                if(nivel_debug<=1){
                                    fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                    fprintf(fichero_log,"[INFO] El contexto %s ya existe\n",contexto);
                                    fclose(fichero_log);
                                }
                            }
                        }
                        // si la orden es borrar....
                        else if(orden==orden_borrar){
                            if(borrarContexto((char *)tabla_contextos,contexto,tamano_contexto,tamano_tabla_contextos)){
                                if(nivel_debug<=1){
                                    fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                    fprintf(fichero_log,"[INFO] Se borra el contexto %s \n",contexto);
                                    fclose(fichero_log);
                                }
                            }
                            else{
                                if(nivel_debug<=2){
                                    fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                                    fprintf(fichero_log,"[ERROR] No se puede borrar el contexto %s \n",contexto);
                                    fclose(fichero_log);
                                }
                            }
                        }
                    }
                }
            }
            // Si se llega al final del fichero se realiza un sleep y se comprueba si se ha modificado otro fichero
            if(caracter==EOF){
                if(nivel_debug<=0){
                    fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                    fprintf(fichero_log,"[DEBUG] WAIT 2 s\n");
                    fclose(fichero_log);
                }
                //Sleep(20000);
                sleep(2);
                //Compruebo si se ha rotado el log
                char buffer[T_NOMBRE_FICHERO_IN];
                get_ultimo_modificado(buffer);
                if (strcmp(buffer,fichero_in) != 0){
                    fclose(archivo);
                    fichero_in[0]='\0';
                    strcat(fichero_in,buffer);
                    if(nivel_debug<=1){
                        fichero_log = fopen(RUTA_FICHERO_OUT, "a");
                        fprintf(fichero_log,"[INFO] Se abre el fichero: %s\n",fichero_in);
                        fclose(fichero_log);
                    }
                    archivo = fopen(fichero_in,"r");
                }
            }
	}// Volvemos a evaluar lla siguiente linea, bucle infinito a proposito, al disponer de sleep de 2 segundos no deberia dar problemas de rendimiento al sistema
        fclose(archivo);//Realmente nunca se llega a cerrar, pero teniendo en cuenta que el fichero se abre como solo lectura no es un problema demasiado grave
    }
    return 0;
}
