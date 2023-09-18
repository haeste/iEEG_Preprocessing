function Spk = gmb_SpikeDet_V0(path_0, IDs, rFs)
%% HLELP

% gmb_SpikeDet_V0 => Based on [https://doi.org/10.1073/pnas.1911461117]
% locks for spikes on the provided data files. Ideally use files between 30s 
% data and 1min data segments

% Input variables:
%   path_0: Path where 30s data segmets are stored. The folder should contain
%           a subfolder for each subject. The name of the files will be a numeric
%           code. In each Subject files there should be:
%                   1) time_segments_*.csv file with identifier (unnamed) of each 30s
%                   segmet, the starting time and the endingn time.
%                   2) rawInfo_*.mat file with information about segment files
%                   3) raw_#.mat, 30 secods files
%
%   IDs: The IDs (also name of the folder for each subjct) of the subjects
%        of interest to read.
%
%   rFs: Resampling frecuancy fro all the subjects
%
%
% Output Files
%   Spk: array of the same length as subjects considering containing the
%        following fields:
%           1) loc -> cell the size of channels for the specific subject
%                     containing timing where spikes have been found

%% ATTENTION 
% PARFOR implemented on line 140 but not optimized, could run into RAM sortage

%% Input arguments check

if nargin < 1
    % Sourse file of raw iEEG
    %path_0 = '/home/campus.ncl.ac.uk/ngb147/Documents/NCL_Desktop/02_Drug_Red/data/iEEG_Raw/';
    path_0 = uigetdir(cd,'Raw iEEG folder with all subjects');

end


if nargin < 2
    % List of the files present on the recording
    file_lst = dir(path_0);

    % Determine which patients are included
    IDs = {file_lst.name};

    % Remove junc files
    fr_xd = strcmp(IDs, '.') | strcmp(IDs, '..');
    IDs(fr_xd) = [];
end

if isempty(IDs)
    % List of the files present on the recording
    file_lst = dir(path_0);

    % Determine which patients are included
    IDs = {file_lst.name};

    % Remove junc files
    fr_xd = strcmp(IDs, '.') | strcmp(IDs, '..');
    IDs(fr_xd) = [];
end

if nargin < 3
    % Resampling frecuency
    rFs = 256;
end

%% Spike detection Parameters [https://doi.org/10.1073/pnas.1911461117]
% Fisrt Step
% Bandpass filtering
% 42Hz in this case to remove 50Hz line noise
% Similar ratio as 50Hz to remove 60 Hz line noise
bp1_f = [20,42]; 
% Threshold as n-times the STD
tr_n = 3;

% Secodn Step
% Bandpass filtering
bp2_f = [1,35];

% Median rectifing parameter
scl_Rect = 70; % Diving by the median & multipling by this moves the median to "70uV"

% Morphology Criteria
Mrp_crt = [600, 7, 10];

for i=1:length(IDs)
    % File wiht the timings for each segment
    t_fl = dir([path_0,IDs{i},'/*.csv']);

    % Timings for each segment
    T = readtable(fullfile(t_fl(1).folder,t_fl(1).name));

    % All mat files
    aux = dir([path_0,IDs{i},'/*.mat']);

    % Info about channels and fs
    Ri_fl = aux(strcmp({aux.name},['rawInfo_',IDs{i},'.mat']));
    rawInfo = load(fullfile(Ri_fl(1).folder,Ri_fl(1).name));

    % Number of channles
    [nCh,~] = size(rawInfo.channelsKeep);

    % Raw data segments files
    Rd_fl = aux(~strcmp({aux.name},['rawInfo_',IDs{i},'.mat']));

    % Spikes repository
    Spk(i).loc = cell(nCh,1);

    for j=1:length(Rd_fl)
        % Load raw data by 30s segments
        load(fullfile(Rd_fl(j).folder,Rd_fl(j).name));

        % Inital timing for This segment
        sed_cd = Rd_fl(j).name(find(Rd_fl(j).name=='_')+1:end-4);
        t0 = T.start(find(T.Var1==str2num(sed_cd)));

        % Resample to 256Hz
        rEEG = resample(EEG',rFs,rawInfo.fs);

        % Spikde detection
        % step 1 ----------------------------------------------------------
        % Filtering
        fEEG_1 = bandpass(rEEG,bp1_f,rFs);

        % Thresholding
        for k=1:nCh
            s1_xd(:,k) = fEEG_1(:,k)>std(fEEG_1(:,k))*tr_n;
        end

        % step 2 ----------------------------------------------------------
        % Filtering
        fEEG_2 = bandpass(rEEG,bp2_f,rFs);

        % Scaling across all channels; median to 70 uV
        mEEG = fEEG_2/median(abs(fEEG_2(:)))*scl_Rect;
        parfor k=1:nCh
            % Find peaks in this channle
            s = mEEG(:,k);
            [~,lck] = findpeaks(s,'MinPeakDistance',Mrp_crt(3));

            % Generate a template and match it to the Thresholding
            temp = zeros(size(s));
            temp(lck) = 1;

            % Relevant peaks
            Locs = find(temp & s1_xd(:,k));
            if isempty(Locs)
                continue;
            end

            for l=1:length(Locs)
                % Locating Valeys
                [~,aux] = findpeaks(-s((-10:10)+Locs(l)));
                v_lck = [max(aux(aux<11)),min(aux(aux>11))]-11;

                if isempty(v_lck)
                    Locs(i) = 0;
                    continue;

                elseif length(v_lck)==1
                    % What if Just 1 valey?
                    % Not mentioned on referenve
                    % "Mirrorr" the valey
                    v_lck = sort([v_lck,-v_lck]);
                end

                % step 3 --------------------------------------------------
                % Morphology Criteria

                % Criteria of Amplitude
                PK = s(Locs(l));
                VL = s(v_lck+Locs(l));
                Amp = PK-VL;

                % Criteria of duration
                Dur = abs(v_lck')/rFs*1000;

                % Criteria of slope
                Slope = Amp./Dur;

                % Determine is Spike
                Crit = [Amp,Slope,Dur]>Mrp_crt;

                % All criteria on both sides matched
                Locs(l) = Locs(l)*double(sum(Crit(:))==6);
            end

            % Remove not Spikes
            Locs(~Locs) = [];
            if isempty(Locs)
                continue;
            end

            % Storing locations
            Temp_Loc{k} = t0 +...
                (Locs-1)/rFs/(60*60*24);
        end

        %Put it all together
        for k=1:nCh
            Spk(i).loc{k} = [Spk(i).loc{k},Temp_Loc{k}];
        end
    end
end

