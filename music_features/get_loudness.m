function [L] = get_loudness(audio_file, plot_loudness)
% Get loudness
%  [L] = get_loudness(audio_file, plot_loudness)
%  audio_file    : path to an audio file
%  plot_loudness : boolean; plot results
%  L             : array; Time (:,1) Loudness (:,2), Normalized (:,3), Normalized-smoothed (:,4)

if nargin < 2 % Plot by default
    plot_loudness = true;
end

% Read audio
[audio, p.fs] = audioread(audio_file); % sampling rate as p.fs for ma_sone
% Compute loudness using MA Toolbox
[~, L, ~] = ma_sone(audio, p);
L(:,3)    = normalize(L(:,2), 'range'); % Normalized data
L(:,4)    = smooth(L(:,3), 0.03, 'loess'); % 2nd degree polynomial smooth with 3% of samples

% Optional plot
if plot_loudness
    figure('Name','Loudness','NumberTitle','off');
    colororder({'k','k'})
    plot(L(:,1), L(:,2), 'LineStyle', '-',  'LineWidth', 0.8, 'Color', [0   0 180]/255)
    ylabel('Loudness (sone)')
    xlabel('Time (s)')
    yyaxis right
    hold on
    plot(L(:,1), L(:,3), 'LineStyle', '-.', 'LineWidth', 0.2, 'Color', [255 160 0]/255)
    plot(L(:,1), L(:,4), 'LineStyle', '-',  'LineWidth', 3.8, 'Color', [139 0   0]/255)
    ylabel('Normalized Loudness (sone)')
    legend('original', 'normalized', 'smoothed')
end
end