��    B      ,  Y   <      �     �     �     �     �     �  	   �               1  ^   E     �  +   �     �  2   �     ,     ?  !   R     t  
   y  -   �     �     �  �   �     �     �  �   �     g	     �	     �	     �	  	   �	     �	  D   �	  D   *
  7   o
  	   �
  "   �
     �
  *   �
          1     Q     l  E   �  ^   �     /  �   J  =     �   L  %   �        V   -     �     �  z   �  #     2   @  $   s  
   �     �     �     �     �  .   �  1     �  8     �               /  
   B     M     U  !   r     �  E   �     �  5        :  @   W     �     �      �     �  
   �     �  0        E  �   d          .  �   >     	     #     ;     U     d     t  P   �  L   �  G   "     j      |  )   �  /   �     �  &     &   6     ]  X   o  b   �     +  �   F  8     �   L  %   �     �  e        {     �  �   �  $   1  9   V  !   �  
   �     �     �  	   �     �  7   �  6   &         "      %                                  3   #   >                ;          2   (           @          
   0   <   :   .   9      '   1              $                       ,      B       6           5   -   +           !                    =   7   8   )   /   	   A          4      *          &             ?          
The found files:   %s (maybe error)   %s (maybe ok)  MB available space  MB needed space  nothing!  size to be backed up:   to make a back-up! * * * WARNING * * * A recording is currently running. Please stop the recording before trying to start a flashing. Additional backup ->  BACK-UP TOOL, FOR MAKING A COMPLETE BACK-UP Backup done with:  Backup finished and copied to your USB-flashdrive. Create: kerneldump Create: root.ubifs Do you really want to unpack %s ? Exit Flashing:  For flashing your receiver files are needed:
 Full back-up direct to USB Full back-up to the harddisk If you place an USB-stick containing this file then the back-up will be automatically made onto the USB-stick and can be used to restore the current image if necessary. Image creation FAILED! KB per second Most likely this back-up can't be restored because of it's size, it's simply too big to restore. This is a limitation of the bootloader not of the back-up or the BackupSuite. NOT found files for flashing!
 No supported receiver found! Not enough free space on  Only kernel Only root PLEASE READ THIS: Please be patient, a backup will now be made, this will take about:  Please check the manual of the receiver on how to restore the image. Please: DO NOT reboot your STB and turn off the power.
 Run flash Select parameter for start flash!
 Select the folder with backup Show only found image and mtd partitions.
 Simulate (no write) Some information about the task Standard (root and kernel) The content of the folder is: The image or kernel will be flashing and auto booted in few minutes.
 The program will abort, please try another medium with more free space to create your back-up. The program will exit now. There COULD be a problem with restoring this back-up because the size of the back-up comes close to the maximum size. This is a limitation of the bootloader not of the back-up or the BackupSuite. There is NO valid USB-stick found, so I've got nothing to do. There is a valid USB-flashdrive detected in one of the USB-ports, therefore an extra copy of the back-up image will now be copied to that USB-flashdrive. This only takes about 20 seconds..... Time required for this process:  To back-up directly to the USB-stick, the USB-stick MUST contain a file with the name: USB Image created in:  Unzip Warning!
Use at your own risk! Make always a backup before use!
Don't use it if you use multiple ubi volumes in ubi layer! What is new since the last release? Your STB will freeze during the flashing process.
 and there is made an extra copy in:  available  backupstick or backupstick.txt current:  %s minutes not found, the backup process will be aborted! ofgwrite will stop enigma2 now to run the flash.
 Project-Id-Version: BackupSuite
Report-Msgid-Bugs-To: 
PO-Revision-Date: 
Last-Translator: Pedro_Newbie <backupsuite@outlook.com>
Language-Team: Vytenis P. <vyteniui@gmail.com>
Language: lt
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Poedit-SourceCharset: UTF-8
X-Generator: Poedit 2.1.1
Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2);
 
Surasti failai:   %s (galbūt klaida)   %s (galbūt gerai)  MB laisvos vietos  MB reikia  nieko!  atsarginės kopijos dydis:   kad padaryti atsarginę kopiją! * * * DĖMESIO * * * Vyksta įrašymas. Prieš atvaizdo įdiegimą, nutraukite įrašymą. Papildoma kopija ->  ATSARGINIO KOPIJAVIMO ĮRANKIS PILNOMS KOPIJOMS KURTI Atsarginė kopija padaryta:  Atsarginis kopijavimas baigtas, kopija įkelta į USB laikmeną. Sukurti: kerneldump Sukurti: root.ubifs Ar tikrai norite išskleisti %s? Užverti Diegiama:  Įdiegimui reikalingi failai:
 Pilna atsarginė kopija tiesiai į USB laikmeną Pilna atsarginė kopija į HDD Jei prijungsite USB laikmeną su šiuo failu, į ją bus automatiškai sukurta atsarginė kopija ir prireikus, ši laikmena gali būti naudojama atkurti dabartinį atvaizdą. Atvaizdo sukurti NEPAVYKO! KB per sekundę Greičiausiai šios atsarginės kopijos nebegalima atkurti dėl jos dydžio - ji tiesiog per didelė, kad atkurti. Tai ne atvaizdo ir ne šio kopijavimo įrankio, bet OS paleidimo programos apribojimas. Failų diegimui NERASTA!
 Nerasta tinkamo imtuvo! Nepakanka laisvos vietos  Tik branduolį Tik pagrindinį PERSKAITYKITE : Būkite kantrūs, atsarginė kopija tuojau bus padaryta. Tai užtruks maždaug:  Kaip atkurti sistemos atvaizdą, žiūrėkite savo aparato vartotojo vadove. NEPALEIDINĖKITE aparato iš naujo ir NEIŠJUNKITE maitinimo įtampos.
 Pradėti diegimą Pasirinkite diegimo parametrus!
 Pasirinkite katalogą su atsargine kopija Rodyti tik rastą atvaizdą ir MTD skaidinius.
 Imituoti (be įrašymo) Šiek tiek informacijos apie užduotį Standartinis (atvaizdas ir branduolys) Katalogo turinys: Atvaizdas, arba branduolys bus įdiegtas ir automatiškai pasileis po kelių minučių.
 Veiksmas bus nutrauktas, atsarginei kopijai pasirinkite kitą laikmeną su daugiau laisvos vietos. Programa dabar užsidarys. GALI būti problemų su šios atsarginės kopijos atkūrimu, nes jos dydis jau priartėja prie maksimalaus leistino. Tai ne atvaizdo ir ne šio kopijavimo įrankio, bet OS paleidimo programos apribojimas. Tinkamų USB laikmenų nerasta, todėl nėra ką daryti. Viename iš USB prievadų aptikta tinkama USB laikmena, todėl papildoma atsarginė atvaizdo kopija bus nukopijuota į tą USB laikmeną. Tai truks tik apie 20 sekundžių.... Šis procesas užtruko:  Kad atsarginę kopiją daryti tiesiai į USB atmintinę, USB laikmenoje TURI BŪTI failas pavadinimu: USB atvaizdas sukurtas:  Išskleisti Įspėjimas!
Naudokite savo atsakomybe! Prieš naudojimą, visada padarykite atsarginę kopiją!
Nenaudokite jo, jei naudojate  keliatomius UBI! Kas naujo nuo paskutinio išleidimo? Diegimo metu jūsų imtuvas nustos reaguoti į komandas.
 ir padaryta papildoma kopija į:  prieinama  backupstick, arba backupstick.txt dabar: %s min. nerasta, atsarginio kopijavimo procesas bus nutrauktas! ofgwrite dabar sustabdys enigma2 ir pradės diegimą.
 